package com.example.demo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import com.example.demo.model.Prediction;

public interface PredictionRepository extends JpaRepository<Prediction, Long> {
}