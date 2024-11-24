from flask import render_template
from flask_login import login_required
from app.main import main_bp
from app.models.study_group import StudyGroup

@main_bp.route('/')
@login_required
def index():
    study_groups = StudyGroup.query.all()

    print(study_groups)

    return render_template('index.html', study_groups=study_groups)