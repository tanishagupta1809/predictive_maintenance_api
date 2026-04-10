import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.*;

public class LoginServlet extends HttpServlet {

    protected void doPost(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {

        String username = req.getParameter("username");

        HttpSession session = req.getSession();
        session.setAttribute("user", username);

        res.sendRedirect("dashboard");
    }
}