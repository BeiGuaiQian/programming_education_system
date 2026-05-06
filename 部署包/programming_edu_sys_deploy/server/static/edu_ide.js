(function () {
  const MONACO_BASE = "https://cdn.jsdelivr.net/npm/monaco-editor@0.52.2/min/vs";

  const escapeHTML = (value) => String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

  const debounce = (fn, delay) => {
    let timer = null;
    return (...args) => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => fn(...args), delay);
    };
  };

  const loadMonaco = () => new Promise((resolve, reject) => {
    if (window.monaco) {
      resolve(window.monaco);
      return;
    }
    if (!window.require) {
      reject(new Error("Monaco loader is unavailable"));
      return;
    }
    window.require.config({ paths: { vs: MONACO_BASE } });
    window.require(["vs/editor/editor.main"], () => resolve(window.monaco), reject);
  });

  window.createEduIDE = async function createEduIDE(options) {
    const textarea = options.textarea;
    const apiFetch = options.apiFetch;
    const statusEl = options.statusEl;
    const root = document.createElement("div");
    root.className = "edu-ide-shell";

    const editorBox = document.createElement("div");
    editorBox.className = "edu-ide-editor";
    const panel = document.createElement("aside");
    panel.className = "edu-ide-panel";
    panel.innerHTML = `
      <section class="edu-ide-section">
        <div class="edu-ide-title">实时诊断</div>
        <div class="edu-ide-empty">开始输入后，我会标出语法错误、warning 和复杂度。</div>
      </section>
    `;
    root.appendChild(editorBox);
    root.appendChild(panel);
    textarea.insertAdjacentElement("afterend", root);

    let monacoEditor = null;
    let decorations = [];
    let complexityWidgets = [];
    let latestComplexityBlocks = [];
    let latestAnalysis = { diagnostics: [], complexity_blocks: [] };
    let failedSubmitCount = 0;
    let submitCount = 0;
    let startedAt = Date.now();

    const contextPayload = () => ({
      context_type: options.contextTypeGetter ? options.contextTypeGetter() : "general",
      target_id: options.targetIdGetter ? options.targetIdGetter() : null,
      expected_function: options.expectedFunctionGetter ? options.expectedFunctionGetter() : "",
      requirements: options.requirementsGetter ? options.requirementsGetter() : []
    });

    const getValue = () => monacoEditor ? monacoEditor.getValue() : textarea.value;
    const setValue = (value) => {
      if (monacoEditor) {
        monacoEditor.setValue(value || "");
      }
      textarea.value = value || "";
      updateStatus();
      scheduleAnalyze();
    };
    const focus = () => {
      if (monacoEditor) monacoEditor.focus();
      else textarea.focus();
    };
    const updateStatus = () => {
      const value = getValue();
      const lines = value.split("\n").length;
      const diagnostics = latestAnalysis.diagnostics || [];
      const errors = diagnostics.filter(item => item.severity === "error").length;
      const warnings = diagnostics.filter(item => item.severity === "warning").length;
      if (statusEl) {
        statusEl.textContent = `${lines} 行 / ${value.length} 字符 · ${errors} 错误 / ${warnings} 警告 · Ctrl/Cmd + Enter 提交`;
      }
    };

    const renderPanel = (analysis, stuck = null) => {
      const diagnostics = analysis.diagnostics || [];
      const blocks = analysis.complexity_blocks || [];
      const diagnosticHTML = diagnostics.length
        ? diagnostics.map(item => `
          <div class="edu-ide-item ${escapeHTML(item.severity)}">
            <strong>${item.severity === "error" ? "红线" : "黄线"} · 第 ${escapeHTML(item.line)} 行</strong><br>
            ${escapeHTML(item.message)}<br>
            <span>${escapeHTML(item.suggestion || "")}</span>
          </div>
        `).join("")
        : '<div class="edu-ide-empty">暂无语法错误或 warning。</div>';
      const complexityHTML = blocks.length
        ? blocks.map(item => `
          <div class="edu-ide-item info">
            <strong>第 ${escapeHTML(item.line_start)}-${escapeHTML(item.line_end)} 行 · ${escapeHTML(item.complexity)}</strong><br>
            ${escapeHTML(item.reason)}<br>
            <span>置信度：${escapeHTML(item.confidence)}</span>
          </div>
        `).join("")
        : '<div class="edu-ide-empty">暂未检测到明显循环或排序复杂度块。</div>';
      const stuckHTML = stuck && stuck.stuck
        ? `<section class="edu-ide-section"><div class="edu-ide-title">卡住提示</div><div class="edu-ide-item warning">${escapeHTML(stuck.hint)}<br>${(stuck.reasons || []).map(escapeHTML).join("<br>")}</div></section>`
        : "";
      panel.innerHTML = `
        <section class="edu-ide-section">
          <div class="edu-ide-title">实时诊断</div>
          ${diagnosticHTML}
        </section>
        <section class="edu-ide-section">
          <div class="edu-ide-title">复杂度提示</div>
          ${complexityHTML}
        </section>
        ${stuckHTML}
      `;
    };

    const applyMonacoMarkers = (analysis) => {
      if (!monacoEditor || !window.monaco) return;
      const model = monacoEditor.getModel();
      const markers = (analysis.diagnostics || []).map(item => ({
        severity: item.severity === "error"
          ? window.monaco.MarkerSeverity.Error
          : window.monaco.MarkerSeverity.Warning,
        startLineNumber: Number(item.line || 1),
        startColumn: Number(item.column || 1),
        endLineNumber: Number(item.end_line || item.line || 1),
        endColumn: Number(item.end_column || item.column || 2),
        message: `${item.message}${item.suggestion ? "\n建议：" + item.suggestion : ""}`,
        code: item.code || ""
      }));
      window.monaco.editor.setModelMarkers(model, "edu-ide", markers);
      decorations = monacoEditor.deltaDecorations(decorations, (analysis.complexity_blocks || []).map(item => ({
        range: new window.monaco.Range(item.line_start, 1, item.line_end, 1),
        options: {
          isWholeLine: true,
          className: "edu-ide-complexity",
          hoverMessage: { value: `${item.complexity}: ${item.reason}` }
        }
      })));
      renderComplexityWidgets(analysis.complexity_blocks || []);
    };

    const clearComplexityWidgets = () => {
      if (!monacoEditor) return;
      complexityWidgets.forEach(widget => monacoEditor.removeContentWidget(widget));
      complexityWidgets = [];
    };

    const renderComplexityWidgets = (blocks) => {
      if (!monacoEditor || !window.monaco) return;
      latestComplexityBlocks = blocks || [];
      clearComplexityWidgets();
      const model = monacoEditor.getModel();
      latestComplexityBlocks.forEach((item, index) => {
        const lineNumber = Number(item.line_end || item.line_start || 1);
        const node = document.createElement("div");
        node.className = "edu-ide-complexity-widget";
        node.title = item.reason || "";
        node.innerHTML = `
          <span>${escapeHTML(item.complexity)}</span>
          <small>第 ${escapeHTML(item.line_start)}-${escapeHTML(item.line_end)} 行</small>
        `;
        const widget = {
          getId: () => `edu-ide-complexity-${index}-${lineNumber}`,
          getDomNode: () => node,
          getPosition: () => ({
            position: {
              lineNumber,
              column: Math.max(1, model.getLineMaxColumn(lineNumber))
            },
            preference: [window.monaco.editor.ContentWidgetPositionPreference.EXACT]
          })
        };
        complexityWidgets.push(widget);
        monacoEditor.addContentWidget(widget);
        monacoEditor.layoutContentWidget(widget);
      });
    };

    const analyze = async () => {
      const code = getValue();
      textarea.value = code;
      if (!apiFetch) return latestAnalysis;
      try {
        latestAnalysis = await apiFetch("/ide/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, ...contextPayload() })
        });
        applyMonacoMarkers(latestAnalysis);
        renderPanel(latestAnalysis);
        updateStatus();
      } catch (_) {
      }
      return latestAnalysis;
    };

    const checkStuck = async () => {
      if (!apiFetch) return;
      const durationSeconds = Math.round((Date.now() - startedAt) / 1000);
      if (durationSeconds < 90 && failedSubmitCount < 2) return;
      try {
        const stuck = await apiFetch("/ide/stuck-check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            code: getValue(),
            ...contextPayload(),
            duration_seconds: durationSeconds,
            submit_count: submitCount,
            failed_submit_count: failedSubmitCount,
            diagnostics: latestAnalysis.diagnostics || []
          })
        });
        renderPanel(latestAnalysis, stuck);
      } catch (_) {
      }
    };

    const scheduleAnalyze = debounce(analyze, 650);
    const scheduleStuck = debounce(checkStuck, 2500);

    const onChange = () => {
      textarea.value = getValue();
      updateStatus();
      scheduleAnalyze();
      scheduleStuck();
      if (options.onChange) options.onChange(getValue());
    };

    try {
      const monaco = await loadMonaco();
      textarea.style.display = "none";
      monacoEditor = monaco.editor.create(editorBox, {
        value: textarea.value || "",
        language: "python",
        theme: "vs-dark",
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        tabSize: 4,
        insertSpaces: true,
        scrollBeyondLastLine: false,
        wordWrap: "off",
        wordWrapOverride1: "off",
        wordWrapOverride2: "off",
        scrollbar: {
          horizontal: "auto",
          vertical: "auto",
          alwaysConsumeMouseWheel: false
        },
        glyphMargin: true,
        quickSuggestions: false
      });
      monacoEditor.onDidChangeModelContent(onChange);
      monacoEditor.onDidScrollChange(() => {
        complexityWidgets.forEach(widget => monacoEditor.layoutContentWidget(widget));
      });
      monacoEditor.onDidLayoutChange(() => {
        complexityWidgets.forEach(widget => monacoEditor.layoutContentWidget(widget));
      });
      monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
        if (options.onSubmit) options.onSubmit();
      });
    } catch (_) {
      root.classList.add("edu-ide-fallback");
      editorBox.remove();
      textarea.style.display = "block";
      root.insertBefore(textarea, panel);
      textarea.addEventListener("input", onChange);
      textarea.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && options.onSubmit) {
          event.preventDefault();
          options.onSubmit();
        }
      });
    }

    window.setInterval(checkStuck, 30000);
    updateStatus();
    scheduleAnalyze();

    return {
      getValue,
      setValue,
      focus,
      analyze,
      getLatestAnalysis: () => latestAnalysis,
      markSubmitResult: (passed) => {
        submitCount += 1;
        if (!passed) failedSubmitCount += 1;
        else failedSubmitCount = 0;
        checkStuck();
      },
      renderSubmitFeedback: (feedback) => {
        if (!feedback) return;
        const list = (items) => items && items.length
          ? `<ul>${items.map(item => `<li>${escapeHTML(item.message || item)}</li>`).join("")}</ul>`
          : "<div class=\"edu-ide-empty\">暂无。</div>";
        panel.insertAdjacentHTML("afterbegin", `
          <section class="edu-ide-feedback">
            <h4>提交后智能建议</h4>
            <div>${escapeHTML(feedback.summary || "")}</div>
            <strong>需要修改的要点</strong>
            ${list(feedback.fix_points || [])}
            <strong>风格提升建议</strong>
            ${list(feedback.style_suggestions || [])}
            <div>${escapeHTML(feedback.next_hint || "")}</div>
          </section>
        `);
      }
    };
  };
})();
