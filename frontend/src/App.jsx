import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Layout from "./components/Layout.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import ReportIssue from "./pages/ReportIssue.jsx";
import MyComplaints from "./pages/MyComplaints.jsx";
import ComplaintDetail from "./pages/ComplaintDetail.jsx";
import TrackComplaint from "./pages/TrackComplaint.jsx";
import AuthorityLogin from "./pages/AuthorityLogin.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import OfficerQueue from "./pages/OfficerQueue.jsx";
import OfficerDetail from "./pages/OfficerDetail.jsx";
import MapExplorer from "./pages/MapExplorer.jsx";
import Officers from "./pages/Officers.jsx";

function Guard({ roles, children }) {
  const { user } = useAuth();
  const loc = useLocation();
  if (!user) {
    const to = roles?.includes("officer") || roles?.includes("admin") ? "/authority/login" : "/login";
    return <Navigate to={to} state={{ from: loc.pathname }} replace />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={user.role === "citizen" ? "/app/complaints" : "/authority"} replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/track" element={<TrackComplaint />} />
        <Route path="/app/report" element={<Guard roles={["citizen"]}><ReportIssue /></Guard>} />
        <Route path="/app/complaints" element={<Guard roles={["citizen"]}><MyComplaints /></Guard>} />
        <Route path="/app/complaints/:id" element={<Guard roles={["citizen"]}><ComplaintDetail /></Guard>} />
        <Route path="/authority/login" element={<AuthorityLogin />} />
        <Route path="/authority" element={<Guard roles={["officer", "admin"]}><Dashboard /></Guard>} />
        <Route path="/authority/queue" element={<Guard roles={["officer", "admin"]}><OfficerQueue /></Guard>} />
        <Route path="/authority/complaints/:id" element={<Guard roles={["officer", "admin"]}><OfficerDetail /></Guard>} />
        <Route path="/authority/map" element={<Guard roles={["officer", "admin"]}><MapExplorer /></Guard>} />
        <Route path="/authority/officers" element={<Guard roles={["admin"]}><Officers /></Guard>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
