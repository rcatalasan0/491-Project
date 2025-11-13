"""
Additional ML Test Cases - Add these to test_model_training.py
"""

@pytest.mark.ml
class TestMLModelValidation:
    """Additional model validation tests"""
    
    def test_model_handles_different_time_periods(self, sample_ml_training_data):
        """ML-009: Test model with different training periods"""
        try:
            from src.ml.predictor import StockPredictor
            
            periods = [180, 365, 730]  # 6 months, 1 year, 2 years
            
            for period in periods:
                data = sample_ml_training_data[-period:]
                predictor = StockPredictor()
                
                predictor.train(data, epochs=5)
                predictions = predictor.predict(data, days=7)
                
                assert len(predictions) == 7, f"Failed for {period} days"
                assert all(p > 0 for p in predictions)
                
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_handles_volatile_market(self):
        """ML-010: Test model with high volatility data"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            # Create highly volatile data
            dates = pd.date_range(end='2024-12-31', periods=365)
            np.random.seed(42)
            volatile_prices = 450 + np.random.normal(0, 50, 365)  # High std dev
            
            volatile_data = pd.DataFrame({
                'Date': dates,
                'Close': volatile_prices,
                'Open': volatile_prices + np.random.normal(0, 10, 365),
                'High': volatile_prices + abs(np.random.normal(20, 10, 365)),
                'Low': volatile_prices - abs(np.random.normal(20, 10, 365)),
                'Volume': np.random.randint(1000000, 10000000, 365)
            }).set_index('Date')
            
            predictor = StockPredictor()
            predictor.train(volatile_data, epochs=10)
            predictions = predictor.predict(volatile_data, days=7)
            
            assert len(predictions) == 7
            # Predictions should still be reasonable despite volatility
            assert all(200 < p < 700 for p in predictions)
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_rejects_invalid_data(self):
        """ML-011: Test model rejects invalid input data"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            predictor = StockPredictor()
            
            # Empty dataframe
            empty_data = pd.DataFrame()
            with pytest.raises(Exception):
                predictor.train(empty_data, epochs=5)
            
            # Missing required columns
            invalid_data = pd.DataFrame({
                'Date': pd.date_range(end='2024-12-31', periods=100),
                'Close': [450] * 100
                # Missing Open, High, Low, Volume
            })
            with pytest.raises(Exception):
                predictor.train(invalid_data, epochs=5)
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_prediction_trends(self, sample_ml_training_data):
        """ML-012: Verify predictions follow reasonable trends"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            predictor.train(sample_ml_training_data, epochs=10)
            predictions = predictor.predict(sample_ml_training_data, days=30)
            
            assert len(predictions) == 30
            
            # Check predictions don't have unrealistic jumps
            for i in range(1, len(predictions)):
                daily_change = abs(predictions[i] - predictions[i-1])
                percent_change = (daily_change / predictions[i-1]) * 100
                
                # Daily change should be less than 20%
                assert percent_change < 20, \
                    f"Unrealistic daily change: {percent_change:.2f}%"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")


@pytest.mark.ml
class TestMLDataPreprocessing:
    """Test data preprocessing and feature engineering"""
    
    def test_data_normalization_range(self, sample_ml_training_data):
        """ML-013: Test data is normalized to [0, 1] range"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            normalized = predictor.normalize_data(sample_ml_training_data)
            
            for col in ['Close', 'Open', 'High', 'Low']:
                if col in normalized.columns:
                    assert normalized[col].min() >= 0
                    assert normalized[col].max() <= 1
            
        except (ImportError, AttributeError):
            pytest.skip("Normalization not implemented")
    
    
    def test_feature_extraction_creates_indicators(self, sample_ml_training_data):
        """ML-014: Test technical indicators are created"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            features = predictor.extract_features(sample_ml_training_data)
            
            # Check for common technical indicators
            expected_features = ['MA_7', 'MA_30', 'RSI', 'MACD']
            
            for feature in expected_features:
                if feature in features.columns:
                    print(f"✓ Feature present: {feature}")
                    assert features[feature].notna().sum() > 0
            
        except (ImportError, AttributeError):
            pytest.skip("Feature extraction not implemented")
    
    
    def test_moving_average_calculation(self, sample_ml_training_data):
        """ML-015: Test moving average calculations"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            features = predictor.extract_features(sample_ml_training_data)
            
            if 'MA_7' in features.columns:
                # MA should be smooth (less volatile than raw prices)
                price_volatility = sample_ml_training_data['Close'].std()
                ma_volatility = features['MA_7'].std()
                
                assert ma_volatility < price_volatility, \
                    "Moving average should be smoother than raw prices"
            
        except (ImportError, AttributeError):
            pytest.skip("Moving average not implemented")
    
    
    def test_handles_outliers_in_data(self):
        """ML-016: Test model handles extreme outliers"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            # Create data with outliers
            dates = pd.date_range(end='2024-12-31', periods=365)
            prices = np.full(365, 450.0)
            prices[100] = 1000  # Extreme spike
            prices[200] = 100   # Extreme drop
            
            outlier_data = pd.DataFrame({
                'Date': dates,
                'Close': prices,
                'Open': prices * 0.99,
                'High': prices * 1.02,
                'Low': prices * 0.98,
                'Volume': [1000000] * 365
            }).set_index('Date')
            
            predictor = StockPredictor()
            predictor.train(outlier_data, epochs=5)
            predictions = predictor.predict(outlier_data, days=7)
            
            # Predictions should not be wildly affected by outliers
            assert all(300 < p < 600 for p in predictions), \
                "Model too sensitive to outliers"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")


@pytest.mark.ml
class TestMLModelPerformance:
    """Test model performance metrics"""
    
    def test_model_mse_within_threshold(self, sample_ml_training_data):
        """ML-017: Test Mean Squared Error is acceptable"""
        try:
            from src.ml.predictor import StockPredictor
            from sklearn.metrics import mean_squared_error
            
            predictor = StockPredictor()
            
            train_size = int(len(sample_ml_training_data) * 0.8)
            train = sample_ml_training_data[:train_size]
            test = sample_ml_training_data[train_size:]
            
            predictor.train(train, epochs=20)
            predictions = predictor.predict(test, days=len(test))
            
            mse = mean_squared_error(test['Close'].values, predictions)
            rmse = np.sqrt(mse)
            
            avg_price = test['Close'].mean()
            rmse_threshold = avg_price * 0.10  # 10% of average
            
            assert rmse < rmse_threshold, \
                f"RMSE {rmse:.2f} exceeds {rmse_threshold:.2f}"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_mae_within_threshold(self, sample_ml_training_data):
        """ML-018: Test Mean Absolute Error is acceptable"""
        try:
            from src.ml.predictor import StockPredictor
            from sklearn.metrics import mean_absolute_error
            
            predictor = StockPredictor()
            
            train_size = int(len(sample_ml_training_data) * 0.8)
            train = sample_ml_training_data[:train_size]
            test = sample_ml_training_data[train_size:]
            
            predictor.train(train, epochs=20)
            predictions = predictor.predict(test, days=len(test))
            
            mae = mean_absolute_error(test['Close'].values, predictions)
            
            avg_price = test['Close'].mean()
            mae_threshold = avg_price * 0.05  # 5% of average
            
            assert mae < mae_threshold, \
                f"MAE ${mae:.2f} exceeds ${mae_threshold:.2f}"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_directional_accuracy(self, sample_ml_training_data):
        """ML-019: Test model predicts direction correctly (up/down)"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            
            train_size = int(len(sample_ml_training_data) * 0.8)
            train = sample_ml_training_data[:train_size]
            test = sample_ml_training_data[train_size:]
            
            predictor.train(train, epochs=20)
            predictions = predictor.predict(test, days=len(test)-1)
            
            # Calculate directional accuracy
            actual_direction = np.diff(test['Close'].values) > 0
            predicted_direction = np.diff(predictions) > 0
            
            # At least 50% directional accuracy
            directional_accuracy = np.mean(actual_direction == predicted_direction)
            
            assert directional_accuracy > 0.50, \
                f"Directional accuracy {directional_accuracy:.2%} too low"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")


@pytest.mark.ml
class TestMLModelRobustness:
    """Test model robustness and edge cases"""
    
    def test_model_with_minimal_data(self):
        """ML-020: Test model with minimum required data points"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            # Minimum data (e.g., 60 days)
            min_dates = pd.date_range(end='2024-12-31', periods=60)
            min_data = pd.DataFrame({
                'Date': min_dates,
                'Close': [450 + i*0.5 for i in range(60)],
                'Open': [449 + i*0.5 for i in range(60)],
                'High': [452 + i*0.5 for i in range(60)],
                'Low': [448 + i*0.5 for i in range(60)],
                'Volume': [1000000] * 60
            }).set_index('Date')
            
            predictor = StockPredictor()
            predictor.train(min_data, epochs=5)
            predictions = predictor.predict(min_data, days=7)
            
            assert len(predictions) == 7
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_consistency_across_runs(self, sample_ml_training_data):
        """ML-021: Test model produces consistent results"""
        try:
            from src.ml.predictor import StockPredictor
            
            # Train model twice with same data
            predictor1 = StockPredictor()
            predictor1.train(sample_ml_training_data, epochs=10)
            pred1 = predictor1.predict(sample_ml_training_data.tail(50), days=7)
            
            predictor2 = StockPredictor()
            predictor2.train(sample_ml_training_data, epochs=10)
            pred2 = predictor2.predict(sample_ml_training_data.tail(50), days=7)
            
            # Results should be similar (within 5%)
            for p1, p2 in zip(pred1, pred2):
                diff_percent = abs(p1 - p2) / p1 * 100
                assert diff_percent < 5, \
                    f"Inconsistent predictions: {p1:.2f} vs {p2:.2f}"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_with_flat_market(self):
        """ML-022: Test model with no trend (flat market)"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            # Flat market data (price stays constant)
            dates = pd.date_range(end='2024-12-31', periods=365)
            flat_data = pd.DataFrame({
                'Date': dates,
                'Close': [450 + np.random.normal(0, 2) for _ in range(365)],
                'Open': [449 + np.random.normal(0, 2) for _ in range(365)],
                'High': [452 + np.random.normal(0, 2) for _ in range(365)],
                'Low': [448 + np.random.normal(0, 2) for _ in range(365)],
                'Volume': [1000000] * 365
            }).set_index('Date')
            
            predictor = StockPredictor()
            predictor.train(flat_data, epochs=10)
            predictions = predictor.predict(flat_data, days=7)
            
            # Predictions should stay near 450
            assert all(440 < p < 460 for p in predictions)
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_with_strong_uptrend(self):
        """ML-023: Test model recognizes strong upward trend"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            # Strong uptrend data
            dates = pd.date_range(end='2024-12-31', periods=365)
            uptrend_data = pd.DataFrame({
                'Date': dates,
                'Close': [400 + i*0.5 for i in range(365)],
                'Open': [399 + i*0.5 for i in range(365)],
                'High': [402 + i*0.5 for i in range(365)],
                'Low': [398 + i*0.5 for i in range(365)],
                'Volume': [1000000] * 365
            }).set_index('Date')
            
            predictor = StockPredictor()
            predictor.train(uptrend_data, epochs=10)
            predictions = predictor.predict(uptrend_data, days=7)
            
            # Predictions should continue upward trend
            assert predictions[-1] > predictions[0], \
                "Model should recognize upward trend"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_with_strong_downtrend(self):
        """ML-024: Test model recognizes strong downward trend"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            # Strong downtrend data
            dates = pd.date_range(end='2024-12-31', periods=365)
            downtrend_data = pd.DataFrame({
                'Date': dates,
                'Close': [600 - i*0.5 for i in range(365)],
                'Open': [601 - i*0.5 for i in range(365)],
                'High': [603 - i*0.5 for i in range(365)],
                'Low': [599 - i*0.5 for i in range(365)],
                'Volume': [1000000] * 365
            }).set_index('Date')
            
            predictor = StockPredictor()
            predictor.train(downtrend_data, epochs=10)
            predictions = predictor.predict(downtrend_data, days=7)
            
            # Predictions should continue downward trend
            assert predictions[-1] < predictions[0], \
                "Model should recognize downward trend"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")


@pytest.mark.ml
@pytest.mark.slow
class TestMLModelAdvanced:
    """Advanced ML model tests"""
    
    def test_model_long_term_predictions(self, sample_ml_training_data):
        """ML-025: Test 30-day predictions"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            predictor.train(sample_ml_training_data, epochs=10)
            predictions = predictor.predict(sample_ml_training_data, days=30)
            
            assert len(predictions) == 30
            
            # Long-term predictions should be reasonable
            last_price = sample_ml_training_data['Close'].iloc[-1]
            for pred in predictions:
                # Within ±30% of last price
                assert 0.7 * last_price < pred < 1.3 * last_price
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_with_different_stocks(self):
        """ML-026: Test model works with different stock patterns"""
        try:
            from src.ml.predictor import StockPredictor
            import pandas as pd
            
            # Simulate different stocks with different characteristics
            stocks = {
                'tech': {'base': 200, 'volatility': 15, 'trend': 0.3},
                'stable': {'base': 50, 'volatility': 2, 'trend': 0.05},
                'penny': {'base': 5, 'volatility': 1, 'trend': -0.1}
            }
            
            for stock_type, params in stocks.items():
                dates = pd.date_range(end='2024-12-31', periods=365)
                
                trend = np.linspace(0, params['trend']*365, 365)
                noise = np.random.normal(0, params['volatility'], 365)
                prices = params['base'] + trend + noise
                
                stock_data = pd.DataFrame({
                    'Date': dates,
                    'Close': prices,
                    'Open': prices * 0.99,
                    'High': prices * 1.02,
                    'Low': prices * 0.98,
                    'Volume': [1000000] * 365
                }).set_index('Date')
                
                predictor = StockPredictor()
                predictor.train(stock_data, epochs=5)
                predictions = predictor.predict(stock_data, days=7)
                
                assert len(predictions) == 7, f"Failed for {stock_type}"
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
    
    
    def test_model_update_with_new_data(self, sample_ml_training_data):
        """ML-027: Test incremental model updates"""
        try:
            from src.ml.predictor import StockPredictor
            
            # Initial training
            initial_data = sample_ml_training_data[:500]
            predictor = StockPredictor()
            predictor.train(initial_data, epochs=10)
            
            # Update with new data
            new_data = sample_ml_training_data[500:]
            predictor.update(new_data, epochs=5)
            
            predictions = predictor.predict(sample_ml_training_data, days=7)
            assert len(predictions) == 7
            
        except (ImportError, AttributeError):
            pytest.skip("Model update not implemented")
    
    
    def test_model_feature_importance(self, sample_ml_training_data):
        """ML-028: Test feature importance analysis"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            predictor.train(sample_ml_training_data, epochs=10)
            
            # Get feature importance
            importance = predictor.get_feature_importance()
            
            assert importance is not None
            assert len(importance) > 0
            
            # Most important features should have higher scores
            assert max(importance.values()) > min(importance.values())
            
        except (ImportError, AttributeError):
            pytest.skip("Feature importance not implemented")
    
    
    def test_model_confidence_scores(self, sample_ml_training_data):
        """ML-029: Test prediction confidence scores"""
        try:
            from src.ml.predictor import StockPredictor
            
            predictor = StockPredictor()
            predictor.train(sample_ml_training_data, epochs=10)
            
            predictions = predictor.predict_with_confidence(
                sample_ml_training_data, days=7
            )
            
            for pred in predictions:
                assert 'predicted_price' in pred
                assert 'confidence' in pred
                assert 0 <= pred['confidence'] <= 1
            
        except (ImportError, AttributeError):
            pytest.skip("Confidence scores not implemented")
    
    
    def test_model_ensemble_predictions(self, sample_ml_training_data):
        """ML-030: Test ensemble model predictions"""
        try:
            from src.ml.predictor import StockPredictor
            
            # Train multiple models
            models = []
            for i in range(3):
                predictor = StockPredictor()
                predictor.train(sample_ml_training_data, epochs=10)
                models.append(predictor)
            
            # Get predictions from all models
            all_predictions = []
            for model in models:
                preds = model.predict(sample_ml_training_data, days=7)
                all_predictions.append(preds)
            
            # Ensemble average
            ensemble_pred = np.mean(all_predictions, axis=0)
            
            assert len(ensemble_pred) == 7
            
        except ImportError:
            pytest.skip("ML predictor not implemented")
