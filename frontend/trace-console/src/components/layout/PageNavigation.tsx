import { Link, useLocation } from "react-router-dom";
import { DEFAULT_CONSOLE_ROUTE, getBreadcrumbLabels } from "../../config/route.config";
import { UI_TEXT } from "../../constants/uiText";

export function PageNavigation() {
  const location = useLocation();
  const breadcrumb = getBreadcrumbLabels(location.pathname);

  return (
    <nav className="page-navigation" aria-label="页面导航">
      <Link to={DEFAULT_CONSOLE_ROUTE}>{UI_TEXT.nav.overview}</Link>
      <span>/</span>
      {breadcrumb.map((item, index) => (
        <span className={index === breadcrumb.length - 1 ? "page-navigation-current" : ""} key={`${item}-${index}`}>
          {item}
          {index < breadcrumb.length - 1 ? " /" : ""}
        </span>
      ))}
    </nav>
  );
}
