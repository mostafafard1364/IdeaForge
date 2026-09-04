"""
IdeaForge - Experiment Framework

Manages research experiments with persistence and tracking.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd


class ExperimentStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass
class Experiment:
    """Research experiment definition."""
    id: str
    name: str
    hypothesis: str
    description: str = ""
    dataset: str = ""
    symbol: str = ""
    timeframe: str = ""
    engine_version: str = "0.1.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = ExperimentStatus.DRAFT.value
    created_at: str = ""
    updated_at: str = ""
    result_summary: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experiment':
        return cls(**data)


class ExperimentRegistry:
    """
    Registry for managing experiments.
    
    Persists experiments to disk for research history.
    """
    
    def __init__(self, base_path: str = "experiments"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._experiments: Dict[str, Experiment] = {}
        self._load_all()
    
    def create(
        self,
        name: str,
        hypothesis: str,
        description: str = "",
        dataset: str = "",
        symbol: str = "",
        timeframe: str = "",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Experiment:
        """Create a new experiment."""
        exp_id = self._generate_id()
        
        experiment = Experiment(
            id=exp_id,
            name=name,
            hypothesis=hypothesis,
            description=description,
            dataset=dataset,
            symbol=symbol,
            timeframe=timeframe,
            parameters=parameters or {},
            status=ExperimentStatus.DRAFT.value
        )
        
        self._experiments[exp_id] = experiment
        self._save(experiment)
        
        return experiment
    
    def get(self, exp_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self._experiments.get(exp_id)
    
    def update(self, exp_id: str, **kwargs) -> Optional[Experiment]:
        """Update experiment fields."""
        exp = self._experiments.get(exp_id)
        if not exp:
            return None
        
        for key, value in kwargs.items():
            if hasattr(exp, key):
                setattr(exp, key, value)
        
        exp.updated_at = datetime.utcnow().isoformat()
        self._save(exp)
        
        return exp
    
    def list_all(self) -> List[Experiment]:
        """List all experiments."""
        return list(self._experiments.values())
    
    def list_by_status(self, status: str) -> List[Experiment]:
        """List experiments by status."""
        return [e for e in self._experiments.values() if e.status == status]
    
    def delete(self, exp_id: str) -> bool:
        """Delete an experiment."""
        if exp_id in self._experiments:
            exp_path = self.base_path / exp_id
            if exp_path.exists():
                import shutil
                shutil.rmtree(exp_path)
            del self._experiments[exp_id]
            return True
        return False
    
    def _generate_id(self) -> str:
        """Generate unique experiment ID."""
        count = len(self._experiments) + 1
        return f"EXP-{count:03d}"
    
    def _save(self, experiment: Experiment):
        """Save experiment to disk."""
        exp_path = self.base_path / experiment.id
        exp_path.mkdir(parents=True, exist_ok=True)
        
        config_path = exp_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(experiment.to_dict(), f, indent=2)
    
    def _load_all(self):
        """Load all experiments from disk."""
        if not self.base_path.exists():
            return
        
        for exp_dir in self.base_path.iterdir():
            if exp_dir.is_dir():
                config_path = exp_dir / "config.json"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        data = json.load(f)
                        experiment = Experiment.from_dict(data)
                        self._experiments[experiment.id] = experiment
