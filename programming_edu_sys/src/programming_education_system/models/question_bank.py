# src/programming_education_system/models/question_bank.py
"""
题库数据模型
"""
import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """难度级别"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuestionType(Enum):
    """题目类型"""
    CODING = "coding"  # 编程题
    MULTIPLE_CHOICE = "multiple_choice"  # 选择题
    TEXT_ANSWER = "text_answer"  # 简答题
    DEBUGGING = "debugging"  # 调试题
    ALGORITHM = "algorithm"  # 算法题


class Question:
    """题目实体类"""

    def __init__(self, id: int, topic: str, content: str, difficulty: DifficultyLevel,
                 question_type: QuestionType, answer: str = "", hints: List[str] = None,
                 examples: List[Dict[str, str]] = None, tags: List[str] = None,
                 created_time: str = None, updated_time: str = None,
                 usage_count: int = 0, success_rate: float = 0.0,
                 source: str = "system", metadata: Dict[str, Any] = None):
        self.id = id
        self.topic = topic
        self.content = content
        self.difficulty = difficulty
        self.question_type = question_type
        self.answer = answer
        self.hints = hints or []
        self.examples = examples or []
        self.tags = tags or []
        self.created_time = created_time or datetime.now().isoformat()
        self.updated_time = updated_time or datetime.now().isoformat()
        self.usage_count = usage_count
        self.success_rate = success_rate
        self.source = source
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "topic": self.topic,
            "content": self.content,
            "difficulty": self.difficulty.value,
            "question_type": self.question_type.value,
            "answer": self.answer,
            "hints": self.hints,
            "examples": self.examples,
            "tags": self.tags,
            "created_time": self.created_time,
            "updated_time": self.updated_time,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "source": self.source,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """从字典创建"""
        return cls(
            id=data["id"],
            topic=data["topic"],
            content=data["content"],
            difficulty=DifficultyLevel(data["difficulty"]),
            question_type=QuestionType(data["question_type"]),
            answer=data.get("answer", ""),
            hints=data.get("hints", []),
            examples=data.get("examples", []),
            tags=data.get("tags", []),
            created_time=data.get("created_time"),
            updated_time=data.get("updated_time"),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0),
            source=data.get("source", "system"),
            metadata=data.get("metadata", {})
        )


class QuestionBank:
    """题库管理器"""

    def __init__(self, db_path: str = "question_bank.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建题目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                difficulty TEXT NOT NULL CHECK(difficulty IN ('beginner', 'intermediate', 'advanced')),
                question_type TEXT NOT NULL CHECK(question_type IN ('coding', 'multiple_choice', 'text_answer', 'debugging', 'algorithm')),
                answer TEXT DEFAULT '',
                hints TEXT DEFAULT '[]',  -- 存储为JSON数组
                examples TEXT DEFAULT '[]',  -- 存储为JSON数组
                tags TEXT DEFAULT '[]',  -- 存储为JSON数组
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                source TEXT DEFAULT 'system',
                metadata TEXT DEFAULT '{}',  -- 存储为JSON对象
                content_hash TEXT UNIQUE  -- 内容哈希，用于去重
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_tags ON questions(tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_usage ON questions(usage_count)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_success_rate ON questions(success_rate)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_hash ON questions(content_hash)')

        conn.commit()
        conn.close()
        logger.info(f"题库数据库已初始化: {self.db_path}")

    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def add_question(self, topic: str, content: str, difficulty: DifficultyLevel,
                     question_type: QuestionType, answer: str = "", hints: List[str] = None,
                     examples: List[Dict[str, str]] = None, tags: List[str] = None,
                     source: str = "system", metadata: Dict[str, Any] = None) -> int:
        """添加题目"""
        try:
            content_hash = self._generate_content_hash(content)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO questions 
                (topic, content, difficulty, question_type, answer, hints, examples, tags, source, metadata, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                topic,
                content,
                difficulty.value,
                question_type.value,
                answer,
                json.dumps(hints or [], ensure_ascii=False),
                json.dumps(examples or [], ensure_ascii=False),
                json.dumps(tags or [], ensure_ascii=False),
                source,
                json.dumps(metadata or {}, ensure_ascii=False),
                content_hash
            ))

            # 获取插入的ID（如果是新题目）
            if cursor.lastrowid:
                question_id = cursor.lastrowid
            else:
                # 如果是重复题目，获取现有ID
                cursor.execute('SELECT id FROM questions WHERE content_hash = ?', (content_hash,))
                result = cursor.fetchone()
                question_id = result[0] if result else None

            conn.commit()
            conn.close()

            if question_id:
                logger.info(f"题目已添加/更新: ID={question_id}, 主题={topic}, 难度={difficulty.value}")
            else:
                logger.warning(f"题目添加失败，可能是重复内容")

            return question_id

        except Exception as e:
            logger.error(f"添加题目失败: {e}")
            return None

    def get_question(self, question_id: int) -> Optional[Question]:
        """获取题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return self._row_to_question(result)
            return None

        except Exception as e:
            logger.error(f"获取题目失败: {e}")
            return None

    def get_questions_by_filters(self, topic: str = None, difficulty: DifficultyLevel = None,
                                 question_type: QuestionType = None, tags: List[str] = None,
                                 limit: int = 10, offset: int = 0) -> List[Question]:
        """根据条件筛选题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = "SELECT * FROM questions WHERE 1=1"
            params = []

            if topic:
                query += " AND topic = ?"
                params.append(topic)

            if difficulty:
                query += " AND difficulty = ?"
                params.append(difficulty.value)

            if question_type:
                query += " AND question_type = ?"
                params.append(question_type.value)

            if tags:
                # 使用JSON函数检查tags数组是否包含指定标签
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("json_extract(tags, '$') LIKE ?")
                    params.append(f'%"{tag}"%')
                query += " AND (" + " OR ".join(tag_conditions) + ")"

            query += " ORDER BY usage_count DESC, success_rate DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()

            return [self._row_to_question(row) for row in results]

        except Exception as e:
            logger.error(f"筛选题目失败: {e}")
            return []

    def search_questions(self, keyword: str, limit: int = 10) -> List[Question]:
        """搜索题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            search_term = f"%{keyword}%"
            cursor.execute('''
                SELECT * FROM questions 
                WHERE content LIKE ? OR topic LIKE ? OR json_extract(tags, '$') LIKE ?
                ORDER BY usage_count DESC 
                LIMIT ?
            ''', (search_term, search_term, search_term, limit))

            results = cursor.fetchall()
            conn.close()

            return [self._row_to_question(row) for row in results]

        except Exception as e:
            logger.error(f"搜索题目失败: {e}")
            return []

    def update_question_usage(self, question_id: int, success: bool = True):
        """更新题目使用统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 获取当前统计
            cursor.execute('SELECT usage_count, success_rate FROM questions WHERE id = ?', (question_id,))
            result = cursor.fetchone()

            if result:
                usage_count, current_success_rate = result
                new_usage_count = usage_count + 1

                # 计算新的成功率
                success_count = current_success_rate * usage_count
                if success:
                    success_count += 1
                new_success_rate = success_count / new_usage_count

                # 更新记录
                cursor.execute('''
                    UPDATE questions 
                    SET usage_count = ?, success_rate = ?, updated_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_usage_count, new_success_rate, question_id))

                conn.commit()

            conn.close()

        except Exception as e:
            logger.error(f"更新题目使用统计失败: {e}")

    def get_popular_questions(self, topic: str = None, limit: int = 10) -> List[Question]:
        """获取热门题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if topic:
                cursor.execute('''
                    SELECT * FROM questions 
                    WHERE topic = ? 
                    ORDER BY usage_count DESC, success_rate DESC 
                    LIMIT ?
                ''', (topic, limit))
            else:
                cursor.execute('''
                    SELECT * FROM questions 
                    ORDER BY usage_count DESC, success_rate DESC 
                    LIMIT ?
                ''', (limit,))

            results = cursor.fetchall()
            conn.close()

            return [self._row_to_question(row) for row in results]

        except Exception as e:
            logger.error(f"获取热门题目失败: {e}")
            return []

    def get_questions_by_success_rate(self, min_rate: float = 0.0, max_rate: float = 1.0,
                                      topic: str = None, limit: int = 10) -> List[Question]:
        """根据成功率筛选题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if topic:
                cursor.execute('''
                    SELECT * FROM questions 
                    WHERE topic = ? AND success_rate BETWEEN ? AND ?
                    ORDER BY success_rate DESC
                    LIMIT ?
                ''', (topic, min_rate, max_rate, limit))
            else:
                cursor.execute('''
                    SELECT * FROM questions 
                    WHERE success_rate BETWEEN ? AND ?
                    ORDER BY success_rate DESC
                    LIMIT ?
                ''', (min_rate, max_rate, limit))

            results = cursor.fetchall()
            conn.close()

            return [self._row_to_question(row) for row in results]

        except Exception as e:
            logger.error(f"根据成功率筛选题目失败: {e}")
            return []

    def delete_question(self, question_id: int) -> bool:
        """删除题目"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
            conn.commit()
            conn.close()

            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"题目已删除: ID={question_id}")

            return deleted

        except Exception as e:
            logger.error(f"删除题目失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取题库统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            stats = {}

            # 总题目数
            cursor.execute('SELECT COUNT(*) FROM questions')
            stats['total_questions'] = cursor.fetchone()[0]

            # 按主题统计
            cursor.execute('SELECT topic, COUNT(*) FROM questions GROUP BY topic')
            stats['questions_by_topic'] = dict(cursor.fetchall())

            # 按难度统计
            cursor.execute('SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty')
            stats['questions_by_difficulty'] = dict(cursor.fetchall())

            # 按类型统计
            cursor.execute('SELECT question_type, COUNT(*) FROM questions GROUP BY question_type')
            stats['questions_by_type'] = dict(cursor.fetchall())

            # 平均使用次数和成功率
            cursor.execute('SELECT AVG(usage_count), AVG(success_rate) FROM questions')
            avg_usage, avg_success = cursor.fetchone()
            stats['average_usage_count'] = round(avg_usage or 0, 2)
            stats['average_success_rate'] = round(avg_success or 0, 2)

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def _row_to_question(self, row) -> Question:
        """将数据库行转换为Question对象"""
        return Question(
            id=row[0],
            topic=row[1],
            content=row[2],
            difficulty=DifficultyLevel(row[3]),
            question_type=QuestionType(row[4]),
            answer=row[5],
            hints=json.loads(row[6]) if row[6] else [],
            examples=json.loads(row[7]) if row[7] else [],
            tags=json.loads(row[8]) if row[8] else [],
            created_time=row[9],
            updated_time=row[10],
            usage_count=row[11],
            success_rate=row[12],
            source=row[13],
            metadata=json.loads(row[14]) if row[14] else {}
        )

    def batch_import_questions(self, questions_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """批量导入题目"""
        try:
            imported = 0
            skipped = 0
            errors = 0

            for question_data in questions_data:
                try:
                    question_id = self.add_question(
                        topic=question_data['topic'],
                        content=question_data['content'],
                        difficulty=DifficultyLevel(question_data['difficulty']),
                        question_type=QuestionType(question_data.get('question_type', 'coding')),
                        answer=question_data.get('answer', ''),
                        hints=question_data.get('hints', []),
                        examples=question_data.get('examples', []),
                        tags=question_data.get('tags', []),
                        source=question_data.get('source', 'import'),
                        metadata=question_data.get('metadata', {})
                    )

                    if question_id:
                        imported += 1
                    else:
                        skipped += 1

                except Exception as e:
                    logger.error(f"导入题目失败: {e}")
                    errors += 1

            return {
                'imported': imported,
                'skipped': skipped,
                'errors': errors,
                'total_processed': len(questions_data)
            }

        except Exception as e:
            logger.error(f"批量导入失败: {e}")
            return {'imported': 0, 'skipped': 0, 'errors': len(questions_data), 'total_processed': len(questions_data)}

    def export_questions(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """导出题目"""
        try:
            questions = self.get_questions_by_filters(
                topic=filters.get('topic'),
                difficulty=filters.get('difficulty'),
                question_type=filters.get('question_type'),
                tags=filters.get('tags'),
                limit=filters.get('limit', 1000)
            )

            return [q.to_dict() for q in questions]

        except Exception as e:
            logger.error(f"导出题目失败: {e}")
            return []