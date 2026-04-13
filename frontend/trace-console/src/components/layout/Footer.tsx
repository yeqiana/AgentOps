import { UI_TEXT } from '../../constants/uiText';

export function Footer() {
  return (
    <footer className="layout-footer">
      <span>{UI_TEXT.shell.footer}</span>
      <span>Web Admin · React + TypeScript + Vite</span>
    </footer>
  );
}
