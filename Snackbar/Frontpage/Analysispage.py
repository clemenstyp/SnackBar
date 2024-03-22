from flask import render_template

from Snackbar import app
from Snackbar.Helper.Analysis import get_analysis


@app.route('/analysis')
def analysis():
    content, tags_hours_labels = get_analysis()
    return render_template('analysis.html', content=content, tagsHoursLabels=tags_hours_labels)


@app.route('/analysis/slide')
def analysis_slide():
    content, tags_hours_labels = get_analysis()
    return render_template('analysisSlide.html', content=content, tagsHoursLabels=tags_hours_labels)
