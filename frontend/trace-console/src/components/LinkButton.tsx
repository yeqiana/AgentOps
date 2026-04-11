import { Link } from "react-router-dom";

interface LinkButtonProps {
  to: string;
  children: string;
}

export function LinkButton({ to, children }: LinkButtonProps) {
  return (
    <Link className="button" to={to}>
      {children}
    </Link>
  );
}
