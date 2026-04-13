import { useState } from "react";

interface PageHintBarProps {
  message: string;
}

export function PageHintBar({ message }: PageHintBarProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <button className="page-hint-toggle" type="button" onClick={() => setCollapsed(false)}>
        显示页面提示
      </button>
    );
  }

  return (
    <section className="page-hint-bar">
      <p>{message}</p>
      <button type="button" onClick={() => setCollapsed(true)}>
        收起
      </button>
    </section>
  );
}
