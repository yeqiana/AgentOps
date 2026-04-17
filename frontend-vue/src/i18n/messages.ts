export const messages = {
  "zh-CN": {
    app: {
      routeTitle: "ChatGPT 重设计"
    },
    sidebar: {
      aria: "聊天侧边栏",
      brandMenu: "打开工作区菜单",
      close: "关闭侧边栏",
      search: "搜索会话",
      searchPlaceholder: "搜索...",
      tabsLabel: "会话视图",
      tabs: {
        chats: "聊天",
        saved: "收藏"
      },
      groups: {
        today: "今天",
        yesterday: "昨天"
      },
      actions: {
        toggleTheme: "切换主题",
        notifications: "通知",
        profile: "个人资料"
      },
      conversations: {
        aiCapabilities: "AI 能力",
        sunriseTime: "日出时间",
        matheranTravel: "马泰兰旅行",
        helpAssignment: "作业帮助",
        slrFilm: "单反胶片相机",
        quadratic: "二次函数绘图",
        toyotaPoetry: "丰田名称诗"
      }
    },
    welcome: {
      plan: "Plus",
      columns: {
        examples: {
          title: "示例",
          entries: [
            "\"用简单的话解释量子计算\"",
            "\"给 10 岁孩子的生日派对来点创意点子\"",
            "\"如何用 Javascript 发起 HTTP 请求？\""
          ]
        },
        capabilities: {
          title: "能力",
          entries: [
            "记住用户在当前对话中较早说过的内容。",
            "允许用户提供后续修正。",
            "经过训练，会拒绝不适当的请求。"
          ]
        },
        limitations: {
          title: "限制",
          entries: [
            "偶尔可能生成不准确的信息。",
            "偶尔可能生成有害指令或带偏见的内容。",
            "对 2021 年之后的世界和事件了解有限。"
          ]
        }
      }
    },
    composer: {
      newChat: "新建聊天",
      voiceInput: "语音输入",
      attachImage: "添加图片",
      typeMessage: "输入消息",
      sendMessage: "发送消息"
    },
    chat: {
      user: "你",
      assistant: "助手"
    }
  },
  en: {
    app: {
      routeTitle: "ChatGPT Redesign"
    },
    sidebar: {
      aria: "Chat sidebar",
      brandMenu: "Open workspace menu",
      close: "Close sidebar",
      search: "Search conversations",
      searchPlaceholder: "Search...",
      tabsLabel: "Conversation views",
      tabs: {
        chats: "CHATS",
        saved: "SAVED"
      },
      groups: {
        today: "Today",
        yesterday: "Yesterday"
      },
      actions: {
        toggleTheme: "Toggle theme",
        notifications: "Notifications",
        profile: "Profile"
      },
      conversations: {
        aiCapabilities: "AI Capabilities",
        sunriseTime: "Sunrise Time",
        matheranTravel: "Matheran Travel",
        helpAssignment: "Help In Assignment",
        slrFilm: "SLR Film Cameras",
        quadratic: "Quadratic Function Plot",
        toyotaPoetry: "Toyota Names Poetry"
      }
    },
    welcome: {
      plan: "Plus",
      columns: {
        examples: {
          title: "Examples",
          entries: [
            "\"Explain quantum computing in simple terms\"",
            "\"Got any creative ideas for a 10 year old's birthday?\"",
            "\"How do I make an HTTP request in Javascript?\""
          ]
        },
        capabilities: {
          title: "Capabilities",
          entries: [
            "Remembers what user said earlier in the conversation.",
            "Allows user to provide follow-up corrections.",
            "Trained to decline inappropriate requests."
          ]
        },
        limitations: {
          title: "Limitations",
          entries: [
            "May occasionally generate incorrect information.",
            "May occasionally produce harmful instructions or biased content.",
            "Limited knowledge of world and events after 2021."
          ]
        }
      }
    },
    composer: {
      newChat: "New Chat",
      voiceInput: "Voice input",
      attachImage: "Attach image",
      typeMessage: "Type message",
      sendMessage: "Send message"
    },
    chat: {
      user: "You",
      assistant: "Assistant"
    }
  }
};

export type AppLocale = keyof typeof messages;
