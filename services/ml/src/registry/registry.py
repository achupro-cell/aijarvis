import os
import json
import joblib
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger
from ..config import settings


@dataclass
class ModelMetadata:
    """Model metadata structure"""
    model_id: str
    model_type: str
    target_type: str
    version: str
    created_at: str
    updated_at: str
    metrics: Dict[str, float]
    feature_names: List[str]
    hyperparameters: Optional[Dict[str, Any]] = None
    training_data_hash: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: str = "active"  # active, deprecated, archived


class ModelRegistry:
    """Model registry for versioned model artifacts"""
    
    def __init__(self):
        self.registry_dir = os.path.join(settings.model_dir, "registry")
        self.models_dir = os.path.join(settings.model_dir, "artifacts")
        self.metadata_file = os.path.join(self.registry_dir, "metadata.json")
        
        # Ensure directories exist
        os.makedirs(self.registry_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Initialize metadata file if it doesn't exist
        self._initialize_metadata()
    
    def _initialize_metadata(self):
        """Initialize metadata file"""
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f, indent=2)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {}
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _generate_model_id(self, model_type: str, target_type: str) -> str:
        """Generate unique model ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{model_type}_{target_type}_{timestamp}"
    
    def _generate_version(self, model_type: str, target_type: str) -> str:
        """Generate next version number"""
        metadata = self._load_metadata()
        
        # Find existing models of same type
        existing_models = [
            meta for meta in metadata.values() 
            if meta['model_type'] == model_type and meta['target_type'] == target_type
        ]
        
        if not existing_models:
            return "1.0.0"
        
        # Extract version numbers and find the highest
        versions = []
        for meta in existing_models:
            try:
                version_parts = meta['version'].split('.')
                version_num = int(version_parts[0]) * 10000 + int(version_parts[1]) * 100 + int(version_parts[2])
                versions.append(version_num)
            except:
                continue
        
        if not versions:
            return "1.0.0"
        
        latest_version = max(versions) + 1
        return f"{latest_version // 10000}.{(latest_version // 100) % 100}.{latest_version % 100}"
    
    def register_model(
        self,
        model: Any,
        model_type: str,
        target_type: str,
        metrics: Dict[str, float],
        feature_names: List[str],
        hyperparameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Register a new model"""
        try:
            # Generate IDs and version
            model_id = self._generate_model_id(model_type, target_type)
            version = self._generate_version(model_type, target_type)
            
            # Create metadata
            metadata = ModelMetadata(
                model_id=model_id,
                model_type=model_type,
                target_type=target_type,
                version=version,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                metrics=metrics,
                feature_names=feature_names,
                hyperparameters=hyperparameters,
                description=description,
                tags=tags or []
            )
            
            # Save model artifact
            artifact_path = os.path.join(self.models_dir, f"{model_id}.joblib")
            model_data = {
                'model': model,
                'feature_names': feature_names,
                'target_type': target_type,
                'metadata': asdict(metadata)
            }
            joblib.dump(model_data, artifact_path)
            
            # Update registry metadata
            registry_metadata = self._load_metadata()
            registry_metadata[model_id] = asdict(metadata)
            self._save_metadata(registry_metadata)
            
            logger.info(f"Model registered successfully: {model_id} (version {version})")
            return model_id
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model by ID"""
        try:
            artifact_path = os.path.join(self.models_dir, f"{model_id}.joblib")
            if not os.path.exists(artifact_path):
                logger.warning(f"Model artifact not found: {model_id}")
                return None
            
            model_data = joblib.load(artifact_path)
            logger.info(f"Model loaded: {model_id}")
            return model_data
            
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return None
    
    def list_models(
        self, 
        model_type: Optional[str] = None,
        target_type: Optional[str] = None,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """List registered models"""
        try:
            metadata = self._load_metadata()
            models = []
            
            for model_id, model_meta in metadata.items():
                if model_meta.get('status') != status:
                    continue
                
                if model_type and model_meta.get('model_type') != model_type:
                    continue
                
                if target_type and model_meta.get('target_type') != target_type:
                    continue
                
                models.append({
                    'model_id': model_id,
                    **model_meta
                })
            
            # Sort by creation date (newest first)
            models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def get_latest_model(
        self, 
        model_type: str, 
        target_type: str,
        status: str = "active"
    ) -> Optional[Dict[str, Any]]:
        """Get the latest model of a specific type"""
        models = self.list_models(model_type, target_type, status)
        if not models:
            return None
        
        latest_model_id = models[0]['model_id']
        return self.get_model(latest_model_id)
    
    def update_model_metadata(
        self, 
        model_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update model metadata"""
        try:
            metadata = self._load_metadata()
            if model_id not in metadata:
                logger.warning(f"Model not found in registry: {model_id}")
                return False
            
            # Update metadata
            metadata[model_id].update(updates)
            metadata[model_id]['updated_at'] = datetime.now().isoformat()
            
            # Save changes
            self._save_metadata(metadata)
            logger.info(f"Model metadata updated: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating model metadata: {e}")
            return False
    
    def delete_model(self, model_id: str, delete_artifact: bool = True) -> bool:
        """Delete a model from registry"""
        try:
            metadata = self._load_metadata()
            if model_id not in metadata:
                logger.warning(f"Model not found in registry: {model_id}")
                return False
            
            # Remove from metadata
            del metadata[model_id]
            self._save_metadata(metadata)
            
            # Delete artifact if requested
            if delete_artifact:
                artifact_path = os.path.join(self.models_dir, f"{model_id}.joblib")
                if os.path.exists(artifact_path):
                    os.remove(artifact_path)
                    logger.info(f"Model artifact deleted: {artifact_path}")
            
            logger.info(f"Model deleted from registry: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting model: {e}")
            return False
    
    def compare_models(self, model_ids: List[str]) -> pd.DataFrame:
        """Compare multiple models"""
        try:
            metadata = self._load_metadata()
            comparison_data = []
            
            for model_id in model_ids:
                if model_id not in metadata:
                    continue
                
                model_meta = metadata[model_id]
                row = {
                    'model_id': model_id,
                    'model_type': model_meta.get('model_type'),
                    'target_type': model_meta.get('target_type'),
                    'version': model_meta.get('version'),
                    'created_at': model_meta.get('created_at'),
                    'status': model_meta.get('status')
                }
                
                # Add metrics
                metrics = model_meta.get('metrics', {})
                for metric_name, metric_value in metrics.items():
                    row[f'metric_{metric_name}'] = metric_value
                
                comparison_data.append(row)
            
            if not comparison_data:
                return pd.DataFrame()
            
            return pd.DataFrame(comparison_data)
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            return pd.DataFrame()
    
    def get_best_model(
        self, 
        model_type: str, 
        target_type: str,
        metric: str = 'accuracy',
        status: str = "active"
    ) -> Optional[Dict[str, Any]]:
        """Get best model based on a specific metric"""
        models = self.list_models(model_type, target_type, status)
        if not models:
            return None
        
        # Find model with best metric
        best_model = None
        best_value = None
        
        for model in models:
            metrics = model.get('metrics', {})
            if metric not in metrics:
                continue
            
            value = metrics[metric]
            if best_value is None or value > best_value:
                best_value = value
                best_model = model
        
        if best_model:
            return self.get_model(best_model['model_id'])
        
        return None
    
    def export_registry(self, export_path: str) -> bool:
        """Export registry metadata to file"""
        try:
            metadata = self._load_metadata()
            with open(export_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Registry exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting registry: {e}")
            return False
    
    def import_registry(self, import_path: str, overwrite: bool = False) -> bool:
        """Import registry metadata from file"""
        try:
            with open(import_path, 'r') as f:
                imported_metadata = json.load(f)
            
            current_metadata = self._load_metadata()
            
            for model_id, model_meta in imported_metadata.items():
                if model_id in current_metadata and not overwrite:
                    logger.warning(f"Model already exists, skipping: {model_id}")
                    continue
                
                current_metadata[model_id] = model_meta
            
            self._save_metadata(current_metadata)
            logger.info(f"Registry imported from: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing registry: {e}")
            return False