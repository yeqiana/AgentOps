import { Link, useLocation } from 'react-router-dom';
import { DEFAULT_CONSOLE_ROUTE, getBreadcrumbLabels } from '../../config/route.config';
import { UI_TEXT } from '../../constants/uiText';

export function PageNavigation() {
  const location = useLocation();
  const breadcrumb = getBreadcrumbLabels(location.pathname);

  return (
    <nav className="page-navigation" aria-label="页面导航">
      <Link className="page-navigation-root" to={DEFAULT_CONSOLE_ROUTE}>
        {UI_TEXT.nav.overview}
      </Link>
      {breadcrumb.map((item, index) => {
        const isCurrent = index === breadcrumb.length - 1;
        return (
          <span className={isCurrent ? 'page-navigation-current' : 'page-navigation-item'} key={`${item}-${index}`}>
            <span className="page-navigation-separator">/</span>
            <span>{item}</span>
          </span>
        );
      })}
    </nav>
  );
}
