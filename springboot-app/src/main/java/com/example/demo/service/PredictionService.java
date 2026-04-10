package com.example.demo.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.example.demo.repository.PredictionRepository;
import com.example.demo.model.Prediction;

@Service
public class PredictionService {

    @Autowired
    private PredictionRepository repo;

    public void savePrediction(Prediction p) {
        repo.save(p);
    }
}