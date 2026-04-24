import { NavLink as RouterNavLink, NavLinkProps } from 'react-router-dom';
import { Ref } from 'react';
import { cn } from '@/lib/utils';

interface NavLinkCompatProps extends Omit<NavLinkProps, 'className'> {
  ref?: Ref<HTMLAnchorElement>;
  className?: string;
  activeClassName?: string;
  pendingClassName?: string;
}

export function NavLink({
  ref,
  className,
  activeClassName,
  pendingClassName,
  to,
  ...props
}: NavLinkCompatProps) {
  return (
    <RouterNavLink
      ref={ref}
      to={to}
      className={({ isActive, isPending }) =>
        cn(
          className,
          isActive && activeClassName,
          isPending && pendingClassName,
        )
      }
      {...props}
    />
  );
}
