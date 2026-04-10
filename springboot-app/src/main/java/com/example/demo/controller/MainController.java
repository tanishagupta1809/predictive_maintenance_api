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
            String json = String.format("""
            {
              "air_temp": %f,
              "process_temp": %f,
              "speed": %f,
              "torque": %f,
              "tool_wear": %f,
              "type": "%s"
            }
            """, airTemp, processTemp, speed, torque, toolWear, type);

            URL url = new URL("http://127.0.0.1:5001/predict");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();

            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);

            OutputStream os = conn.getOutputStream();
            os.write(json.getBytes());
            os.flush();

            BufferedReader br = new BufferedReader(
                    new InputStreamReader(conn.getInputStream())
            );

            String response = br.readLine();

            model.addAttribute("result", response);

            // SAVE HISTORY
            history.add(response);

            // EXTRACT CONFIDENCE (simple parse)
            if (response.contains("confidence")) {
                String conf = response.split("confidence\":")[1].split(",")[0];
                confidenceList.add(Double.parseDouble(conf));
            }

        } catch (Exception e) {
            model.addAttribute("result", "Error: " + e.getMessage());
        }

        model.addAttribute("history", history);
        model.addAttribute("confData", confidenceList);

        return "dashboard";
    }
}