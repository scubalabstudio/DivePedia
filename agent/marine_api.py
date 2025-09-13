from flask import Flask, request, jsonify
import json
import os
from typing import List, Dict
import urllib.parse

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

class MarineDataAPI:
    def __init__(self):
        self.data = {
            'fish': [],
            'sea_slug': [],
            'crustacean': []
        }
        self.load_data()
    
    def load_data(self):
        """Load marine data from JSON files"""
        base_path = "/Users/toru.nakamichi/Desktop/diving_API/creature_data"
        
        files = {
            'fish': 'fish_data.json',
            'sea_slug': 'sea_slug_data.json', 
            'crustacean': 'crustacean_other_data.json'
        }
        
        for category, filename in files.items():
            filepath = os.path.join(base_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.data[category] = json.load(f)
                print(f"Loaded {len(self.data[category])} {category} records")
            except FileNotFoundError:
                print(f"Warning: {filepath} not found")
                self.data[category] = []
    
    def search_by_prefix(self, prefix: str) -> List[Dict]:
        """Search for creatures whose names start with the given prefix"""
        if not prefix:
            return []
        
        results = []
        prefix_lower = prefix.lower()
        
        for category, creatures in self.data.items():
            for creature in creatures:
                name = creature.get('name', '')
                if name.lower().startswith(prefix_lower):
                    result = creature.copy()
                    result['category'] = category
                    results.append(result)
        
        return results

# Initialize data loader
marine_data = MarineDataAPI()

@app.route('/search', methods=['GET'])
def search_creatures():
    """
    Search for creatures by name prefix
    Usage: GET /search?q=ハコ
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'error': 'Query parameter "q" is required',
            'example': '/search?q=ハコ'
        }), 400
    
    # Decode URL-encoded query if needed
    try:
        query = urllib.parse.unquote(query, encoding='utf-8')
    except:
        pass
    
    results = marine_data.search_by_prefix(query)
    
    response = jsonify({
        'query': query,
        'count': len(results),
        'results': results
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    total_records = sum(len(creatures) for creatures in marine_data.data.values())
    return jsonify({
        'status': 'healthy',
        'total_records': total_records,
        'categories': {
            'fish': len(marine_data.data['fish']),
            'sea_slug': len(marine_data.data['sea_slug']),
            'crustacean': len(marine_data.data['crustacean'])
        }
    })

@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'message': 'Marine Creatures API',
        'endpoints': {
            '/search?q=<prefix>': 'Search creatures by name prefix',
            '/health': 'Check API health and data status',
            '/': 'This documentation'
        },
        'example': '/search?q=ハコ'
    })

if __name__ == '__main__':
    print("Starting Marine Creatures API...")
    print("Available endpoints:")
    print("  GET /search?q=<prefix> - Search by name prefix")
    print("  GET /health - Health check")
    print("  GET / - API documentation")
    app.run(debug=True, host='0.0.0.0', port=8080)