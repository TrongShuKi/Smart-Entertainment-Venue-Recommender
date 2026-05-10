import math
from typing import List, Dict, Any

class RecommenderEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "weights": {
                "style": 2.0,
                "mood": 1.0,
                "distance": -0.2
            },
            "weather_rules": {
                "bad_weather_statuses": ["RAIN", "STORM"],
                "restricted_location_types": ["Outdoor"]
            },
            "group_tag_mapping": "Group",
            "max_results": 3
        }

    @staticmethod
    def _calculate_distance(coord1: tuple, coord2: tuple) -> float:
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 2)

    def generate_recommendations(self, user_request: Dict, user_context: Dict, location_database: List[Dict]) -> List[Dict]:
        must_haves = user_request.get('must_haves', {})
        preferences = user_request.get('preferences', {})
        
        valid_locations = []
        for loc in location_database:
            if not (loc.get('open_time', 0) <= user_context['current_time'] <= loc.get('close_time', 24)):
                continue
                
            if 'budget' in must_haves and loc.get('price', 0) > must_haves['budget']:
                continue
                
            is_bad_weather = user_context.get('weather') in self.config['weather_rules']['bad_weather_statuses']
            is_restricted_type = loc.get('type') in self.config['weather_rules']['restricted_location_types']
            if is_bad_weather and is_restricted_type:
                continue
                
            if must_haves.get('category') and loc.get('category') != must_haves['category']:
                continue
            if must_haves.get('district') and loc.get('district') != must_haves['district']:
                continue
                
            if must_haves.get('group_type') and self.config['group_tag_mapping'] not in loc.get('tags', []):
                continue
                
            valid_locations.append(loc)

        scored_locations = []
        for loc in valid_locations:
            score = loc.get('rating', 0.0)
            matched_moods, matched_styles = [], []
            
            loc_tags = loc.get('tags', [])
            for tag in loc_tags:
                if tag in preferences.get('style', []):
                    score += self.config['weights']['style']
                    matched_styles.append(tag)
                elif tag in preferences.get('mood', []):
                    score += self.config['weights']['mood']
                    matched_moods.append(tag)
                    
            distance = self._calculate_distance(user_context['coords'], loc['coords'])
            score += (distance * self.config['weights']['distance'])
            
            scored_locations.append({
                "location_id": loc.get("id"),
                "name": loc.get("name"),
                "total_score": round(score, 2),
                "distance_km": distance,
                "matches": {
                    "moods": matched_moods,
                    "styles": matched_styles
                }
            })

        scored_locations.sort(key=lambda x: (-x['total_score'], x['distance_km']))
        return scored_locations[:self.config['max_results']]
