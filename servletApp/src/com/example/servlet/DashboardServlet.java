import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.*;

public class DashboardServlet extends HttpServlet {

    protected void doGet(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {

        HttpSession session = req.getSession(false);

        if (session == null || session.getAttribute("user") == null) {
            res.sendRedirect("login.html");
            return;
        }

        res.setContentType("text/html");
        PrintWriter out = res.getWriter();

        out.println("<h2>Welcome " + session.getAttribute("user") + "</h2>");
        out.println("<a href='logout'>Logout</a>");
    }
}