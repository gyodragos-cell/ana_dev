import { tool } from "@opencode-ai/plugin";

export const ANAMCPBridge = async ({ client }) => {
  const ANA_MCP_URL = "http://127.0.0.1:8765/mcp";

  async function callANA(toolName, args = {}) {
    const body = JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method: "tools/call",
      params: {
        name: toolName,
        arguments: args
      }
    });

    const headers = { "Content-Type": "application/json" };
    if (process.env.ANA_MCP_KEY) {
      headers["Authorization"] = `Bearer ${process.env.ANA_MCP_KEY}`;
    }

    const resp = await fetch(ANA_MCP_URL, {
      method: "POST",
      headers,
      body
    });
    return await resp.json();
  }

  const tools = {
    ana_browser_control: tool({
      description: "ANA MCP: Browser control - open, inspect, click, type, screenshot.",
      args: {
        operation: tool.schema.string(),
        url: tool.schema.optional(tool.schema.string()),
        selector: tool.schema.optional(tool.schema.string()),
        text: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("browser_control", {
          operation: args.operation,
          ...(args.url && { url: args.url }),
          ...(args.selector && { selector: args.selector }),
          ...(args.text && { text: args.text })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_security_audit: tool({
      description: "ANA MCP: Security audit - scan secrets, static analysis, hash gen.",
      args: {
        operation: tool.schema.string(),
        target: tool.schema.string()
      },
      async execute(args) {
        const result = await callANA("security_audit", {
          operation: args.operation,
          target: args.target
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_network_diag: tool({
      description: "ANA MCP: Network diagnostics - ping, port scan, DNS, IP info.",
      args: {
        operation: tool.schema.string(),
        target: tool.schema.string()
      },
      async execute(args) {
        const result = await callANA("network_diag", {
          operation: args.operation,
          target: args.target
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_memory: tool({
      description: "ANA MCP: Persistent memory - save knowledge, search, errors.",
      args: {
        action: tool.schema.string(),
        query: tool.schema.optional(tool.schema.string()),
        content: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("ana_memory", {
          action: args.action,
          ...(args.query && { query: args.query }),
          ...(args.content && { content: args.content })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),



    ana_advanced_scanner: tool({
      description: "ANA MCP: Advanced security scanner - deep scan, exploit check, stealth recon.",
      args: {
        operation: tool.schema.string(),
        target: tool.schema.string()
      },
      async execute(args) {
        const result = await callANA("advanced_scanner", {
          operation: args.operation,
          target: args.target
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_privacy_shield: tool({
      description: "ANA MCP: Privacy shield - scan telemetry, block tracking, obfuscate.",
      args: {
        operation: tool.schema.string(),
        text: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("privacy_shield", {
          operation: args.operation,
          ...(args.text && { text: args.text })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),



    ana_desktop_capture: tool({
      description: "ANA MCP: Capture desktop screenshot. Returneaza calea catre imagine.",
      args: {
        operation: tool.schema.string()
      },
      async execute(args) {
        const result = await callANA("desktop_capture", {
          operation: args.operation
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_desktop_control: tool({
      description: "ANA MCP: Control desktop - view (screenshot), click_at (x,y), type (text), hotkey (ctrl,c), read_text (OCR), click_text, click_image, move_window.",
      args: {
        operation: tool.schema.string(),
        target: tool.schema.optional(tool.schema.string()),
        window_title: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("desktop_control", {
          operation: args.operation,
          ...(args.target && { target: args.target }),
          ...(args.window_title && { window_title: args.window_title })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_windows_insight: tool({
      description: "ANA MCP: Analiza ferestre active, aplicatii, procese desktop.",
      args: {
        operation: tool.schema.string(),
        query: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("windows_insight", {
          operation: args.operation,
          ...(args.query && { query: args.query })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_windows_uia_bridge: tool({
      description: "ANA MCP: Microsoft UI Automation (Ochi vizuali) - Citeste interfața aplicațiilor Windows și interacționează cu ele nativ (list_windows, inspect_window, click_element, type_text).",
      args: {
        action: tool.schema.string(),
        window_title: tool.schema.optional(tool.schema.string()),
        element_title: tool.schema.optional(tool.schema.string()),
        auto_id: tool.schema.optional(tool.schema.string()),
        control_type: tool.schema.optional(tool.schema.string()),
        text: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("windows_uia_bridge", {
          action: args.action,
          ...(args.window_title && { window_title: args.window_title }),
          ...(args.element_title && { element_title: args.element_title }),
          ...(args.auto_id && { auto_id: args.auto_id }),
          ...(args.control_type && { control_type: args.control_type }),
          ...(args.text && { text: args.text })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_windows_deep_sight: tool({
      description: "ANA MCP: God View - monitorizeaza click-uri, procese, fisiere, ferestre in timp real. Operatii: start_god_view, stop_god_view, get_events, process_tree, system_snapshot, trace_process, hook_process, get_clicks, get_processes, window_tree.",
      args: {
        operation: tool.schema.string(),
        target: tool.schema.optional(tool.schema.string()),
        path: tool.schema.optional(tool.schema.string()),
        duration: tool.schema.optional(tool.schema.number()),
        hook_functions: tool.schema.optional(tool.schema.string()),
        script: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("windows_deep_sight", {
          operation: args.operation,
          ...(args.target && { target: args.target }),
          ...(args.path && { path: args.path }),
          ...(args.duration && { duration: args.duration }),
          ...(args.hook_functions && { hook_functions: args.hook_functions }),
          ...(args.script && { script: args.script })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    }),

    ana_system_control: tool({
      description: "ANA MCP: Control sistem - vitals, processes, disk, network, hardware info.",
      args: {
        operation: tool.schema.string(),
        target: tool.schema.optional(tool.schema.string())
      },
      async execute(args) {
        const result = await callANA("system_control", {
          operation: args.operation,
          ...(args.target && { target: args.target })
        });
        return result?.result?.content?.[0]?.text || JSON.stringify(result);
      }
    })
  };

  await client.app.log({
    body: {
      service: "ana-mcp-bridge",
      level: "info",
      message: "ANA MCP Bridge initialized with 11 core OS-level tools (Desktop Control, UIA, Deep Sight)"
    }
  });

  return { tool: tools };
};
