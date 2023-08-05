from flask import Flask, request, jsonify
from seotools.app import Analyzer

analyzer = Analyzer("https://jamesg.blog/sitemap.xml", load_from_disk=False)

app = Flask(__name__)

@app.route("/analyze")
def analyze():
    query = request.args.get("query")
    allowed_directories = request.args.get("allowed_directories", "")

    if not query:
        return jsonify([])

    if allowed_directories:
        allowed_directories = allowed_directories.split(",")
    
    recommendations = analyzer.recommend_related_content(query, allowed_directories)

    return jsonify(recommendations)

if __name__ == "__main__":
    app.run(debug=True)