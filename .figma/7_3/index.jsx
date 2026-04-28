import React from 'react';

import styles from './index.module.scss';

const Component = () => {
  return (
    <div className={styles.frame}>
      <div className={styles.container7}>
        <div className={styles.container3}>
          <div className={styles.container}>
            <img src="../image/moenxk2c-7lg05st.svg" className={styles.icon} />
          </div>
          <div className={styles.container2}>
            <p className={styles.codeMentor}>CodeMentor</p>
          </div>
        </div>
        <div className={styles.container4}>
          <div className={styles.button}>
            <img src="../image/moenxk2c-lrdxprw.svg" className={styles.icon2} />
            <p className={styles.text}>学习中心</p>
          </div>
          <div className={styles.button2}>
            <img src="../image/moenxk2c-u9fgl8a.svg" className={styles.icon2} />
            <p className={styles.text2}>题库</p>
          </div>
          <div className={styles.button3}>
            <img src="../image/moenxk2c-3y6qw8i.svg" className={styles.icon2} />
            <p className={styles.text2}>AI 助手</p>
          </div>
          <div className={styles.button4}>
            <img src="../image/moenxk2c-q208n6x.svg" className={styles.icon2} />
            <p className={styles.text2}>个人中心</p>
          </div>
        </div>
        <div className={styles.container6}>
          <div className={styles.container5}>
            <p className={styles.u}>U</p>
          </div>
        </div>
      </div>
      <div className={styles.learningPage}>
        <div className={styles.container12}>
          <div className={styles.container8}>
            <div className={styles.heading3}>
              <p className={styles.text3}>课程目录</p>
            </div>
            <div className={styles.paragraph}>
              <p className={styles.text4}>Python 编程基础</p>
            </div>
          </div>
          <div className={styles.container11}>
            <div className={styles.container10}>
              <div className={styles.button5}>
                <img src="../image/moenxk2c-bgef2k1.svg" className={styles.icon3} />
                <p className={styles.text5}>第1章 Python基础</p>
              </div>
              <div className={styles.container9}>
                <div className={styles.button6}>
                  <img
                    src="../image/moenxk2c-4lll6ef.svg"
                    className={styles.icon4}
                  />
                  <p className={styles.text6}>1.1 变量与数据类型</p>
                </div>
                <div className={styles.button7}>
                  <img
                    src="../image/moenxk2c-5fppiel.svg"
                    className={styles.icon4}
                  />
                  <p className={styles.text7}>1.2 运算符与表达式</p>
                </div>
                <div className={styles.button8}>
                  <div className={styles.icon5}>
                    <div className={styles.vector} />
                  </div>
                  <p className={styles.text8}>1.3 条件语句</p>
                </div>
              </div>
            </div>
            <div className={styles.button9}>
              <img src="../image/moenxk2c-zejjzaf.svg" className={styles.icon3} />
              <div className={styles.text10}>
                <p className={styles.text9}>第2章 控制结构</p>
              </div>
            </div>
          </div>
        </div>
        <div className={styles.container21}>
          <div className={styles.container15}>
            <div className={styles.container13}>
              <div className={styles.text11}>
                <p className={styles.text4}>第1章</p>
              </div>
              <div className={styles.text12}>
                <p className={styles.a}>/</p>
              </div>
              <div className={styles.text13}>
                <p className={styles.text4}>运算符与表达式</p>
              </div>
            </div>
            <div className={styles.container14}>
              <div className={styles.heading2}>
                <p className={styles.text14}>运算符与表达式</p>
              </div>
              <div className={styles.badge}>
                <p className={styles.text15}>基础</p>
              </div>
            </div>
            <p className={styles.text16}>教材来源: 《Python程序设计》第2章</p>
          </div>
          <div className={styles.container20}>
            <div className={styles.section}>
              <div className={styles.heading32}>
                <p className={styles.text17}>算术运算符</p>
              </div>
              <div className={styles.paragraph2}>
                <p className={styles.text18}>
                  Python支持常见的算术运算符,包括加(+)、减(-)、乘(*)、除(/)等。
                </p>
              </div>
              <div className={styles.container17}>
                <div className={styles.container16}>
                  <p className={styles.text19}>加法:</p>
                  <div className={styles.code}>
                    <p className={styles.aB}>a + b</p>
                  </div>
                </div>
                <div className={styles.container16}>
                  <p className={styles.text19}>减法:</p>
                  <div className={styles.code}>
                    <p className={styles.aB}>a - b</p>
                  </div>
                </div>
                <div className={styles.container16}>
                  <p className={styles.text19}>乘法:</p>
                  <div className={styles.code}>
                    <p className={styles.aB}>a * b</p>
                  </div>
                </div>
                <div className={styles.container16}>
                  <p className={styles.text19}>除法:</p>
                  <div className={styles.code}>
                    <p className={styles.aB}>a / b</p>
                  </div>
                </div>
              </div>
            </div>
            <div className={styles.section2}>
              <div className={styles.heading4}>
                <p className={styles.codeMentor}>示例代码</p>
              </div>
              <div className={styles.container19}>
                <div className={styles.container18}>
                  <p className={styles.text4}>Python</p>
                </div>
                <div className={styles.codeBlock}>
                  <p className={styles.a10B3PrintAb13PrintA}>
                    a = 10
                    <br />b = 3<br />
                    print(a + b)&nbsp;&nbsp;&nbsp;# 13
                    <br />
                    print(a // b)&nbsp;&nbsp;# 3<br />
                    print(a % b)&nbsp;&nbsp;&nbsp;# 1<br />
                    print(a ** b)&nbsp;&nbsp;# 1000
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className={styles.container25}>
          <div className={styles.container22}>
            <div className={styles.heading42}>
              <p className={styles.codeMentor}>练习: 计算圆的面积</p>
            </div>
            <div className={styles.paragraph3}>
              <p className={styles.text20}>
                编写一个程序,输入半径,计算并输出圆的面积。(π取3.14)
              </p>
            </div>
          </div>
          <div className={styles.container24}>
            <div className={styles.container23}>
              <p className={styles.text21}>代码编辑器</p>
              <div className={styles.button10}>
                <img src="../image/moenxk2c-lq5kan6.svg" className={styles.icon6} />
                <p className={styles.text9}>重置</p>
              </div>
            </div>
            <div className={styles.textArea} />
            <div className={styles.button11}>
              <p className={styles.u}>提交判题</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Component;
