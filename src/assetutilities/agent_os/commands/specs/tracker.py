# ABOUTME: Tracks prompt evolution and version history across agent workflows.
# ABOUTME: Extracted from specs_integration.py PromptEvolutionTracker class.
"""Prompt evolution tracking for agent workflows."""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from assetutilities.agent_os.commands.specs.models import OperationResult

class PromptEvolutionTracker:
    """Tracks prompt usage and evolution over time."""

    def __init__(self, tracking_dir: Path):
        """Initialize prompt evolution tracker.
        
        Args:
            tracking_dir: Directory for storing tracking data
        """
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

    def track_prompt_usage(self, prompt_id: str, usage_data: Dict[str, Any]) -> OperationResult:
        """Track prompt usage statistics.
        
        Args:
            prompt_id: Unique identifier for the prompt
            usage_data: Usage statistics (tokens, quality, timing, etc.)
            
        Returns:
            Operation result
        """
        try:
            tracking_file = self.tracking_dir / f"{prompt_id}.json"
            
            # Load existing data or create new
            if tracking_file.exists():
                with open(tracking_file, 'r') as f:
                    tracking_data = json.load(f)
            else:
                tracking_data = {
                    "prompt_id": prompt_id,
                    "created_at": datetime.now().isoformat(),
                    "usage_history": [],
                    "versions": []
                }
            
            # Add new usage record
            usage_record = {
                **usage_data,
                "timestamp": datetime.now().isoformat()
            }
            tracking_data["usage_history"].append(usage_record)
            tracking_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            with open(tracking_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Tracked usage for prompt '{prompt_id}'",
                data={"tracking_file": str(tracking_file)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to track prompt usage: {e}")

    def get_prompt_statistics(self, prompt_id: str) -> Dict[str, Any]:
        """Get usage statistics for a prompt.
        
        Args:
            prompt_id: Prompt identifier
            
        Returns:
            Statistics dictionary
        """
        tracking_file = self.tracking_dir / f"{prompt_id}.json"
        
        if not tracking_file.exists():
            return {"error": "No tracking data found", "total_uses": 0}
        
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
            
            usage_history = tracking_data.get("usage_history", [])
            
            if not usage_history:
                return {"total_uses": 0}
            
            # Calculate statistics
            total_uses = len(usage_history)
            tokens_used = [u.get("tokens_used", 0) for u in usage_history if "tokens_used" in u]
            quality_scores = [u.get("response_quality", 0) for u in usage_history if "response_quality" in u]
            execution_times = [u.get("execution_time", 0) for u in usage_history if "execution_time" in u]
            
            stats = {
                "prompt_id": prompt_id,
                "total_uses": total_uses,
                "average_tokens": sum(tokens_used) / len(tokens_used) if tokens_used else 0,
                "average_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
                "agents_used": list(set(u.get("agent", "unknown") for u in usage_history)),
                "contexts_used": list(set(u.get("context", "unknown") for u in usage_history)),
                "first_use": usage_history[0].get("timestamp", "unknown"),
                "last_use": usage_history[-1].get("timestamp", "unknown")
            }
            
            return stats
            
        except Exception as e:
            return {"error": f"Failed to calculate statistics: {e}"}

    def suggest_prompt_improvements(self, prompt_id: str, current_prompt: str) -> List[str]:
        """Suggest improvements based on usage patterns.
        
        Args:
            prompt_id: Prompt identifier
            current_prompt: Current prompt text
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        stats = self.get_prompt_statistics(prompt_id)
        
        if "error" in stats:
            return ["No usage data available for analysis"]
        
        # Analyze quality trends
        if stats.get("average_quality", 0) < 0.7:
            suggestions.append("Consider adding more specific instructions to improve response quality")
        
        # Analyze token usage
        if stats.get("average_tokens", 0) > 300:
            suggestions.append("Prompt may be too complex; consider breaking into smaller, focused prompts")
        
        # Analyze execution time
        if stats.get("average_execution_time", 0) > 5.0:
            suggestions.append("Long execution times may indicate overly complex requirements")
        
        # Analyze prompt structure
        if len(current_prompt.split('\n')) < 3:
            suggestions.append("Consider structuring prompt with clear sections (context, task, output format)")
        
        if "{" in current_prompt and "}" in current_prompt:
            variables = re.findall(r'\{(\w+)\}', current_prompt)
            if len(variables) > 5:
                suggestions.append("Many variables detected; ensure all are properly documented")
        
        # Context-specific suggestions
        contexts = stats.get("contexts_used", [])
        if len(contexts) > 3:
            suggestions.append("Prompt used in multiple contexts; consider creating context-specific variants")
        
        return suggestions if suggestions else ["Prompt performance looks good based on current metrics"]

    def track_prompt_version(self, prompt_id: str, version_data: Dict[str, Any]) -> OperationResult:
        """Track a new version of a prompt.
        
        Args:
            prompt_id: Prompt identifier
            version_data: Version information (version, prompt text, changes)
            
        Returns:
            Operation result
        """
        try:
            tracking_file = self.tracking_dir / f"{prompt_id}.json"
            
            if tracking_file.exists():
                with open(tracking_file, 'r') as f:
                    tracking_data = json.load(f)
            else:
                tracking_data = {
                    "prompt_id": prompt_id,
                    "created_at": datetime.now().isoformat(),
                    "usage_history": [],
                    "versions": []
                }
            
            # Add version record
            version_record = {
                **version_data,
                "tracked_at": datetime.now().isoformat()
            }
            tracking_data["versions"].append(version_record)
            tracking_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            with open(tracking_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            
            return OperationResult(success=True, message=f"Tracked version for prompt '{prompt_id}'")
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to track prompt version: {e}")

    def get_evolution_timeline(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get evolution timeline for a prompt.
        
        Args:
            prompt_id: Prompt identifier
            
        Returns:
            Timeline of prompt versions
        """
        tracking_file = self.tracking_dir / f"{prompt_id}.json"
        
        if not tracking_file.exists():
            return []
        
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
            
            return sorted(
                tracking_data.get("versions", []),
                key=lambda x: x.get("timestamp", x.get("tracked_at", ""))
            )
            
        except Exception:
            return []

    def export_tracking_data(self, export_path: Path) -> OperationResult:
        """Export all tracking data.
        
        Args:
            export_path: Path for export file
            
        Returns:
            Operation result
        """
        try:
            export_data = {
                "export_date": datetime.now().isoformat(),
                "prompts": {},
                "summary": {}
            }
            
            # Collect all tracking files
            tracking_files = list(self.tracking_dir.glob("*.json"))
            
            for tracking_file in tracking_files:
                prompt_id = tracking_file.stem
                
                with open(tracking_file, 'r') as f:
                    prompt_data = json.load(f)
                
                export_data["prompts"][prompt_id] = prompt_data
            
            # Generate summary
            total_prompts = len(export_data["prompts"])
            total_uses = sum(len(data.get("usage_history", [])) for data in export_data["prompts"].values())
            
            export_data["summary"] = {
                "total_prompts_tracked": total_prompts,
                "total_usage_records": total_uses,
                "tracking_period": self._get_tracking_period()
            }
            
            # Save export file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Exported tracking data to {export_path}",
                data=export_data["summary"]
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to export tracking data: {e}")

    def _get_tracking_period(self) -> Dict[str, str]:
        """Get the overall tracking period."""
        tracking_files = list(self.tracking_dir.glob("*.json"))
        
        if not tracking_files:
            return {"start": "no data", "end": "no data"}
        
        earliest = datetime.now()
        latest = datetime.min
        
        for tracking_file in tracking_files:
            try:
                with open(tracking_file, 'r') as f:
                    data = json.load(f)
                
                created_at = datetime.fromisoformat(data.get("created_at", ""))
                if created_at < earliest:
                    earliest = created_at
                
                last_updated = datetime.fromisoformat(data.get("last_updated", ""))
                if last_updated > latest:
                    latest = last_updated
                    
            except Exception:
                continue
        
        return {
            "start": earliest.isoformat(),
            "end": latest.isoformat()
        }


