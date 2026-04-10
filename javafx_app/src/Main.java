import javafx.application.Application;
import javafx.geometry.Insets;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;
import javafx.scene.chart.*;
import javafx.scene.control.Label;
import javafx.scene.control.TableView;
import javafx.scene.control.TableColumn;
import java.io.*;
import java.lang.classfile.Label;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.sql.*;

// import javax.swing.table.TableColumn;
// import javax.swing.text.TableView;

public class Main extends Application {

    @Override
    public void start(Stage stage) {

        TextField airTemp = new TextField();
        airTemp.setPromptText("Air Temperature");

        TextField processTemp = new TextField();
        processTemp.setPromptText("Process Temperature");

        TextField speed = new TextField();
        speed.setPromptText("Rotational Speed");

        TextField torque = new TextField();
        torque.setPromptText("Torque");

        TextField toolWear = new TextField();
        toolWear.setPromptText("Tool Wear");

        ComboBox<String> type = new ComboBox<>();
        type.getItems().addAll("L", "M", "H");
        type.setPromptText("Machine Type");

        Button predictBtn = new Button("Predict");

        Label resultLabel = new Label("Result will appear here");

        // ---------------- GRAPH ----------------
        NumberAxis xAxis = new NumberAxis();
        NumberAxis yAxis = new NumberAxis();
        LineChart<Number, Number> chart = new LineChart<>(xAxis, yAxis);
        chart.setTitle("Confidence Trend");

        XYChart.Series<Number, Number> series = new XYChart.Series<>();
        series.setName("Confidence");
        chart.getData().add(series);

        // ---------------- TABLE ----------------
        TableView<String> table = new TableView<>();
        TableColumn<String, String> col = new TableColumn<>("Prediction History");

        col.setCellValueFactory(data ->
                new javafx.beans.property.SimpleStringProperty(data.getValue())
        );

        table.getColumns().add(col);
        table.setPrefHeight(150);

        // ---------------- BUTTON ACTION ----------------
        predictBtn.setOnAction(e -> {
            try {

                // -------- INPUT VALIDATION --------
                if (airTemp.getText().isEmpty() || processTemp.getText().isEmpty() ||
                        speed.getText().isEmpty() || torque.getText().isEmpty() ||
                        toolWear.getText().isEmpty() || type.getValue() == null) {

                    resultLabel.setStyle("-fx-text-fill: orange;");
                    resultLabel.setText("⚠ Please fill all fields");
                    return;
                }

                try {
                    Double.parseDouble(airTemp.getText());
                    Double.parseDouble(processTemp.getText());
                    Double.parseDouble(speed.getText());
                    Double.parseDouble(torque.getText());
                    Double.parseDouble(toolWear.getText());
                } catch (Exception ex) {
                    resultLabel.setStyle("-fx-text-fill: orange;");
                    resultLabel.setText("⚠ Enter valid numbers");
                    return;
                }

                // -------- API CALL --------
                String jsonInput = String.format("""
                {
                  "air_temp": %s,
                  "process_temp": %s,
                  "speed": %s,
                  "torque": %s,
                  "tool_wear": %s,
                  "type": "%s"
                }
                """,
                        airTemp.getText(),
                        processTemp.getText(),
                        speed.getText(),
                        torque.getText(),
                        toolWear.getText(),
                        type.getValue()
                );

                URL url = new URL("http://127.0.0.1:5001/predict");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();

                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);

                try (OutputStream os = conn.getOutputStream()) {
                    os.write(jsonInput.getBytes(StandardCharsets.UTF_8));
                }

                BufferedReader br = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
                );

                StringBuilder response = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    response.append(line.trim());
                }

                String res = response.toString();
                conn.disconnect();

                // -------- PARSE --------
                boolean isFailure = res.contains("\"failure\":1");

                String confidence = "0";
                if (res.contains("confidence")) {
                    int start = res.indexOf("confidence");
                    confidence = res.substring(start).split(":")[1]
                            .replace("}", "")
                            .trim();
                }

                String faultType = "No Failure";
                if (res.contains("fault_type")) {
                    int start = res.indexOf("fault_type");
                    faultType = res.substring(start).split(":")[1]
                            .replace("\"", "")
                            .replace("}", "")
                            .trim();
                }

                // -------- DISPLAY --------
                if (isFailure) {
                    resultLabel.setStyle("-fx-text-fill: red; -fx-font-weight: bold;");
                    resultLabel.setText("⚠ FAILURE DETECTED\nConfidence: " + confidence + "\nFault: " + faultType);
                } else {
                    resultLabel.setStyle("-fx-text-fill: lightgreen; -fx-font-weight: bold;");
                    resultLabel.setText("✓ MACHINE HEALTHY\nConfidence: " + confidence);
                }

                // -------- GRAPH UPDATE --------
                try {
                    double conf = Double.parseDouble(confidence);
                    yAxis.setAutoRanging(false);
                    yAxis.setLowerBound(0);
                    yAxis.setUpperBound(1);
                    yAxis.setTickUnit(0.1);
                    chart.setCreateSymbols(true);
                    series.getData().add(new XYChart.Data<>(series.getData().size() + 1, conf));
                } catch (Exception ignored) {}

                // -------- TABLE UPDATE --------
                String displayText = "Saved ✔ | " + res;
                table.getItems().add(displayText);
                String cleanRow = isFailure ? 
                    "FAILURE | Confidence: " + confidence :
                    "HEALTHY | Confidence: " + confidence;

                table.getItems().add(cleanRow);
                // -------- DATABASE --------
                try {
                    Class.forName("org.sqlite.JDBC");
                    Connection dbConn = DriverManager.getConnection("jdbc:sqlite:predictions.db");

                    Statement stmt = dbConn.createStatement();
                    stmt.executeUpdate("""
                        CREATE TABLE IF NOT EXISTS predictions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            air_temp REAL,
                            process_temp REAL,
                            speed REAL,
                            torque REAL,
                            tool_wear REAL,
                            machine_type TEXT,
                            api_response TEXT
                        );
                    """);

                    PreparedStatement pstmt = dbConn.prepareStatement(
                        "INSERT INTO predictions (air_temp, process_temp, speed, torque, tool_wear, machine_type, api_response) VALUES (?, ?, ?, ?, ?, ?, ?)"
                    );

                    pstmt.setDouble(1, Double.parseDouble(airTemp.getText()));
                    pstmt.setDouble(2, Double.parseDouble(processTemp.getText()));
                    pstmt.setDouble(3, Double.parseDouble(speed.getText()));
                    pstmt.setDouble(4, Double.parseDouble(torque.getText()));
                    pstmt.setDouble(5, Double.parseDouble(toolWear.getText()));
                    pstmt.setString(6, type.getValue());
                    pstmt.setString(7, res);

                    pstmt.executeUpdate();
                    dbConn.close();

                } catch (Exception dbEx) {
                    System.out.println("DB Error: " + dbEx.getMessage());
                }

            } catch (Exception ex) {
                resultLabel.setText("Error: " + ex.getMessage());
            }
        });

        // ---------------- UI STYLING ----------------
        VBox layout = new VBox(15,
                airTemp, processTemp, speed, torque, toolWear,
                type, predictBtn, resultLabel, chart, table
        );

        layout.setPadding(new Insets(25));
        layout.setStyle("-fx-background-color: #f5f7fa;");

       predictBtn.setStyle("""
            -fx-background-color: #4CAF50;
            -fx-text-fill: white;
            -fx-font-size: 14px;
            -fx-background-radius: 8;
        """);

        Scene scene = new Scene(layout, 450, 700);

        stage.setTitle("Predictive Maintenance Dashboard");
        stage.setScene(scene);
        stage.show();
    }

    public static void main(String[] args) {
        launch();
    }
}