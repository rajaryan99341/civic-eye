import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../AuthContext";
function Eye() { return <span className="eye" aria-hidden="true"><span /></span>; }
export default function Layout() {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const authority = loc.pathname.startsWith("/authority");
  return <div className={`shell ${authority ? "authority" : ""}`}>
    <header className="nav">
      <NavLink to={authority ? "/authority" : "/"} className="brand"><Eye />CIVIC EYE</NavLink>
      <nav className="nav-links">
        {!authority && <><NavLink to="/track">Track</NavLink>{user?.role === "citizen" && <><NavLink to="/app/report">Report</NavLink><NavLink to="/app/complaints">My issues</NavLink></>}{!user && <><NavLink to="/login">Citizen sign in</NavLink><NavLink to="/authority/login">Authority</NavLink></>}</>}
        {authority && user && (user.role === "officer" || user.role === "admin") && <><NavLink to="/authority" end>Dashboard</NavLink><NavLink to="/authority/queue">Queue</NavLink><NavLink to="/authority/map">Map</NavLink>{user.role === "admin" && <NavLink to="/authority/officers">Officers</NavLink>}</>}
        {user && <button className="linkish" onClick={logout} type="button">Sign out</button>}
        {!user && authority && <NavLink to="/">Citizen portal</NavLink>}
      </nav>
    </header>
    <Outlet />
    <footer className="footer"><span>CIVIC EYE — SEE THE ISSUE. TRIGGER THE ACTION.</span><span>Citizen + municipal issue operations</span></footer>
  </div>;
}
