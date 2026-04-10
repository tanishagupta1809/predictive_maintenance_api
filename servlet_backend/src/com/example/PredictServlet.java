package com.example;
import javax.servlet.*;
import javax.servlet.http.*;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class PredictServlet extends HttpServlet {

    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        String airTemp = request.getParameter("air_temp");
        String processTemp = request.getParameter("process_temp");
        String speed = request.getParameter("speed");
        String torque = request.getParameter("torque");
        String toolWear = request.getParameter("tool_wear");
        String type = request.getParameter("type");

        // Create JSON for Flask
        String jsonInput = String.format("""
        {
          "air_temp": %s,
          "process_temp": %s,
          "speed": %s,
          "torque": %s,
          "tool_wear": %s,
          "type": "%s"
        }
        """, airTemp, processTemp, speed, torque, toolWear, type);

        // Call Flask API
        URL url = new URL("http://localhost:8080/your-app/predict");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);

        OutputStream os = conn.getOutputStream();
        os.write(jsonInput.getBytes());
        os.flush();

        BufferedReader br = new BufferedReader(
                new InputStreamReader(conn.getInputStream())
        );

        String output = br.readLine();
        
        try {
            Class.forName("org.sqlite.JDBC");
            java.sql.Connection dbConn = java.sql.DriverManager.getConnection("jdbc:sqlite:predictions.db");

            java.sql.PreparedStatement pstmt = dbConn.prepareStatement(
                "INSERT INTO predictions (api_response) VALUES (?)"
            );

            pstmt.setString(1, output);
            pstmt.executeUpdate();

            dbConn.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
        // Return response to client
        response.setContentType("application/json");
        response.getWriter().write(output);
    }
}