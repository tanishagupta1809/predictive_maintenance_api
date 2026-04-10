package com.example.demo.model;

import jakarta.persistence.*;

@Entity
public class Prediction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private double airTemp;
    private double torque;
    private String result;
