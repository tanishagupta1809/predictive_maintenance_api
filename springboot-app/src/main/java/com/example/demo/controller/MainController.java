package com.example.demo.controller;

import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.net.*;
import java.io.*;
import java.util.*;

@Controller
public class MainController {

    // TEMP MEMORY (for graph + history demo)
    private List<String> history = new ArrayList<>();
    private List<Double> confidenceList = new ArrayList<>();

    /**
     * Escape JSON string for safe embedding in HTML attributes
     */
    private String escapeJsonForHtml(String json) {
        if (json == null) return "";
        return json.replace("\"", "&quot;").replace("<", "&lt;").replace(">", "&gt;");
    }

    @GetMapping("/")
    public String loginPage() {
        return "login";
    }

    @PostMapping("/login")
    public String login(@RequestParam String username, HttpSession session) {
        session.setAttribute("user", username);
        return "redirect:/dashboard";
    }

    @GetMapping("/dashboard")
    public String dashboard(HttpSession session, Model model) {
        if (session.getAttribute("user") == null) return "redirect:/";

        model.addAttribute("history", history);
        model.addAttribute("confData", confidenceList);

        return "dashboard";
    }

    @PostMapping("/predict")
    public String predict(
            @RequestParam double airTemp,
            @RequestParam double processTemp,
            @RequestParam double speed,
            @RequestParam double torque,
            @RequestParam double toolWear,
            @RequestParam String type,
            Model model
    ) {

        try {
            String json = String.format(
                "{\"air_temp\": %f, \"process_temp\": %f, \"speed\": %f, \"torque\": %f, \"tool_wear\": %f, \"type\": \"%s\"}",
                airTemp, processTemp, speed, torque, toolWear, type
            );

            URL url = new URL("http://127.0.0.1:5001/predict");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();

            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setRequestProperty("Content-Length", String.valueOf(json.length()));
            conn.setDoOutput(true);
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(json.getBytes("UTF-8"));
                os.flush();
            }

            int responseCode = conn.getResponseCode();
            String response;
            
            if (responseCode == 200) {
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(conn.getInputStream()))) {
                    response = br.readLine();
                }
            } else {
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(conn.getErrorStream()))) {
                    response = br.readLine();
                }
            }

            model.addAttribute("result", response);

            // SAVE HISTORY
            history.add(response);

            // EXTRACT CONFIDENCE (simple parse)
            if (response != null && response.contains("\"failure_confidence\"")) {
                String conf = response.split("\"failure_confidence\":")[1].split(",")[0];
                try {
                    confidenceList.add(Double.parseDouble(conf));
                } catch (NumberFormatException e) {
                    // Skip if can't parse
                }
            }

        } catch (Exception e) {
            model.addAttribute("result", "Error: " + e.getMessage());
            e.printStackTrace();
        }

        model.addAttribute("history", history);
        model.addAttribute("confData", confidenceList);

        return "dashboard";
    }
}