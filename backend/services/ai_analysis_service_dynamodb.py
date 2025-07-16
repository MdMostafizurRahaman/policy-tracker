"""
DynamoDB-based AI Analysis service for policy analysis and scoring.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
import uuid
from config.dynamodb import get_dynamodb
from config.data_constants import POLICY_AREAS
from utils.helpers import calculate_policy_score, calculate_completeness_score

logger = logging.getLogger(__name__)

class AIAnalysisService:
    def __init__(self):
        pass
    
    async def _get_db(self):
        """Get DynamoDB client"""
        return await get_dynamodb()
    
    async def analyze_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a policy submission and provide AI insights"""
        try:
            logger.info("Starting AI policy analysis")
            
            # Calculate basic scores
            policy_score = calculate_policy_score(policy_data)
            completeness_score = calculate_completeness_score(policy_data)
            
            # Analyze policy areas coverage
            covered_areas = set()
            total_policies = 0
            
            for area in policy_data.get('policy_areas', []):
                covered_areas.add(area.get('area_name', ''))
                total_policies += len(area.get('policies', []))
            
            # Calculate coverage percentage
            total_possible_areas = len(POLICY_AREAS)
            coverage_percentage = (len(covered_areas) / total_possible_areas) * 100 if total_possible_areas > 0 else 0
            
            # Generate insights
            insights = []
            
            # Coverage insights
            if coverage_percentage >= 80:
                insights.append({
                    "type": "strength",
                    "category": "coverage",
                    "message": f"Excellent policy coverage across {len(covered_areas)} areas ({coverage_percentage:.1f}%)"
                })
            elif coverage_percentage >= 50:
                insights.append({
                    "type": "improvement",
                    "category": "coverage",
                    "message": f"Good policy coverage, but consider expanding to more areas. Currently covering {coverage_percentage:.1f}%"
                })
            else:
                insights.append({
                    "type": "weakness",
                    "category": "coverage",
                    "message": f"Limited policy coverage ({coverage_percentage:.1f}%). Consider adding policies in more areas"
                })
            
            # Policy quantity insights
            if total_policies >= 20:
                insights.append({
                    "type": "strength",
                    "category": "quantity",
                    "message": f"Strong policy portfolio with {total_policies} total policies"
                })
            elif total_policies >= 10:
                insights.append({
                    "type": "neutral",
                    "category": "quantity",
                    "message": f"Moderate policy portfolio with {total_policies} policies"
                })
            else:
                insights.append({
                    "type": "improvement",
                    "category": "quantity",
                    "message": f"Consider expanding policy portfolio. Currently {total_policies} policies"
                })
            
            # Missing areas analysis
            all_area_names = {area['name'] for area in POLICY_AREAS}
            missing_areas = all_area_names - covered_areas
            
            if missing_areas:
                top_missing = list(missing_areas)[:3]  # Show top 3 missing areas
                insights.append({
                    "type": "suggestion",
                    "category": "missing_areas",
                    "message": f"Consider adding policies in: {', '.join(top_missing)}"
                })
            
            # Quality insights based on completeness
            if completeness_score >= 80:
                insights.append({
                    "type": "strength",
                    "category": "quality",
                    "message": "High quality policy descriptions with good detail"
                })
            elif completeness_score >= 60:
                insights.append({
                    "type": "improvement",
                    "category": "quality",
                    "message": "Policy descriptions could be more detailed for better impact"
                })
            else:
                insights.append({
                    "type": "weakness",
                    "category": "quality",
                    "message": "Policy descriptions need significant improvement for clarity and impact"
                })
            
            # Generate recommendations
            recommendations = []
            
            if coverage_percentage < 70:
                recommendations.append("Expand policy coverage to include more diverse areas")
            
            if total_policies < 15:
                recommendations.append("Increase the number of policies for comprehensive governance")
            
            if completeness_score < 70:
                recommendations.append("Improve policy descriptions with more specific details and implementation plans")
            
            # Add area-specific recommendations
            priority_areas = ["Healthcare", "Education", "Economic Development", "Environment"]
            for area in priority_areas:
                if area not in covered_areas:
                    recommendations.append(f"Consider adding policies in {area} for comprehensive coverage")
            
            analysis_result = {
                "analysis_id": str(uuid.uuid4()),
                "policy_score": policy_score,
                "completeness_score": completeness_score,
                "coverage_percentage": round(coverage_percentage, 1),
                "total_policies": total_policies,
                "covered_areas": list(covered_areas),
                "missing_areas": list(missing_areas),
                "insights": insights,
                "recommendations": recommendations,
                "overall_rating": self._calculate_overall_rating(policy_score, completeness_score, coverage_percentage),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("AI policy analysis completed successfully")
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    def _calculate_overall_rating(self, policy_score: float, completeness_score: float, coverage_percentage: float) -> str:
        """Calculate overall policy rating"""
        combined_score = (policy_score + completeness_score + coverage_percentage) / 3
        
        if combined_score >= 85:
            return "Excellent"
        elif combined_score >= 70:
            return "Good"
        elif combined_score >= 55:
            return "Fair"
        elif combined_score >= 40:
            return "Needs Improvement"
        else:
            return "Poor"
    
    async def get_country_analysis(self, country: str) -> Dict[str, Any]:
        """Get comprehensive analysis for a country's policies"""
        try:
            db = await self._get_db()
            
            # Get all approved policies for the country
            all_policies = await db.scan_table('policies')
            country_policies = [
                p for p in all_policies 
                if p.get('country', '').lower() == country.lower() 
                and p.get('status') == 'approved'
            ]
            
            if not country_policies:
                return {
                    "country": country,
                    "total_policies": 0,
                    "message": "No approved policies found for this country",
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            
            # Aggregate analysis
            total_policies = sum(p.get('total_policies', 0) for p in country_policies)
            avg_policy_score = sum(p.get('score', 0) for p in country_policies) / len(country_policies)
            avg_completeness = sum(p.get('completeness_score', 0) for p in country_policies) / len(country_policies)
            
            # Collect all covered areas
            all_covered_areas = set()
            area_policy_counts = {}
            
            for policy in country_policies:
                for area in policy.get('policy_areas', []):
                    area_name = area.get('area_name', '')
                    all_covered_areas.add(area_name)
                    area_policy_counts[area_name] = area_policy_counts.get(area_name, 0) + len(area.get('policies', []))
            
            # Calculate coverage
            total_possible_areas = len(POLICY_AREAS)
            coverage_percentage = (len(all_covered_areas) / total_possible_areas) * 100 if total_possible_areas > 0 else 0
            
            return {
                "country": country,
                "total_submissions": len(country_policies),
                "total_policies": total_policies,
                "average_policy_score": round(avg_policy_score, 2),
                "average_completeness_score": round(avg_completeness, 2),
                "coverage_percentage": round(coverage_percentage, 1),
                "covered_areas": list(all_covered_areas),
                "policies_by_area": area_policy_counts,
                "overall_rating": self._calculate_overall_rating(avg_policy_score, avg_completeness, coverage_percentage),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Country analysis error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Country analysis failed: {str(e)}")
    
    async def compare_countries(self, countries: List[str]) -> Dict[str, Any]:
        """Compare policy performance across multiple countries"""
        try:
            if len(countries) < 2:
                raise HTTPException(status_code=400, detail="At least 2 countries required for comparison")
            
            country_analyses = []
            for country in countries:
                analysis = await self.get_country_analysis(country)
                if analysis.get('total_policies', 0) > 0:
                    country_analyses.append(analysis)
            
            if len(country_analyses) < 2:
                return {
                    "message": "Insufficient data for comparison",
                    "countries_with_data": [a['country'] for a in country_analyses],
                    "compared_at": datetime.utcnow().isoformat()
                }
            
            # Sort by overall performance
            country_analyses.sort(key=lambda x: x.get('average_policy_score', 0), reverse=True)
            
            # Find best and worst performers
            best_performer = country_analyses[0]
            worst_performer = country_analyses[-1]
            
            # Calculate averages across all countries
            avg_policies = sum(c.get('total_policies', 0) for c in country_analyses) / len(country_analyses)
            avg_score = sum(c.get('average_policy_score', 0) for c in country_analyses) / len(country_analyses)
            avg_coverage = sum(c.get('coverage_percentage', 0) for c in country_analyses) / len(country_analyses)
            
            return {
                "countries_compared": len(country_analyses),
                "comparison_data": country_analyses,
                "best_performer": {
                    "country": best_performer['country'],
                    "score": best_performer.get('average_policy_score', 0)
                },
                "worst_performer": {
                    "country": worst_performer['country'],
                    "score": worst_performer.get('average_policy_score', 0)
                },
                "averages": {
                    "policies": round(avg_policies, 1),
                    "score": round(avg_score, 2),
                    "coverage": round(avg_coverage, 1)
                },
                "compared_at": datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Country comparison error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Country comparison failed: {str(e)}")

# Global instance
ai_analysis_service = AIAnalysisService()
