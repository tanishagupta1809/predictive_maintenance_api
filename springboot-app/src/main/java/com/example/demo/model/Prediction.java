package com.example.demo.model;

import jakarta.persistence.*;

@Entity
public class Prediction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private double airTemp;
    private double processTemp;
    private double speed;
    private double torque;
    private double toolWear;
    private String type;
    private String result;
    private double confidence;

    public Prediction() {}

    public Prediction(double airTemp, double processTemp, double speed, double torque, double toolWear, String type) {
        this.airTemp = airTemp;
        this.processTemp = processTemp;
        this.speed = speed;
        this.torque = torque;
        this.toolWear = toolWear;
        this.type = type;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public double getAirTemp() { return airTemp; }
    public void setAirTemp(double airTemp) { this.airTemp = airTemp; }

    public double getProcessTemp() { return processTemp; }
    public void setProcessTemp(double processTemp) { this.processTemp = processTemp; }

    public double getSpeed() { return speed; }
    public void setSpeed(double speed) { this.speed = speed; }

    public double getTorque() { return torque; }
    public void setTorque(double torque) { this.torque = torque; }

    public double getToolWear() { return toolWear; }
    public void setToolWear(double toolWear) { this.toolWear = toolWear; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getResult() { return result; }
    public void setResult(String result) { this.result = result; }

    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }
}
