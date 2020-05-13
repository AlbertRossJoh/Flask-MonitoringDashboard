from datetime import datetime

from flask import request

from flask_monitoringdashboard import blueprint
from flask_monitoringdashboard.core.auth import secure
from flask_monitoringdashboard.core.date_interval import DateInterval
from flask_monitoringdashboard.core.reporting.questions.median_latency import MedianLatency
from flask_monitoringdashboard.core.reporting.questions.status_code_distribution import (
    StatusCodeDistribution,
)
from flask_monitoringdashboard.database import session_scope
from flask_monitoringdashboard.database.endpoint import get_endpoints


def get_date(p):
    return datetime.utcfromtimestamp(int(request.args.get(p)))


def make_endpoint_summary(endpoint, interval, baseline_interval):
    questions = [MedianLatency(), StatusCodeDistribution()]

    summary = dict(
        endpoint_id=endpoint.id,
        endpoint_name=endpoint.name,
        answers=[],
        has_anything_significant=False,
    )

    for question in questions:
        answer = question.get_answer(endpoint, interval, baseline_interval)

        if answer.is_significant():
            summary['has_anything_significant'] = True

        summary['answers'].append(answer.serialize())

    return summary


@blueprint.route('/api/reporting/make_report', methods=['POST'])
@secure
def make_report():
    arguments = request.json

    try:
        interval = DateInterval(
            datetime.fromtimestamp(int(arguments['interval']['from'])),
            datetime.fromtimestamp(int(arguments['interval']['to'])),
        )

        baseline_interval = DateInterval(
            datetime.fromtimestamp(int(arguments['baseline_interval']['from'])),
            datetime.fromtimestamp(int(arguments['baseline_interval']['to'])),
        )
    except Exception:
        return 'Invalid payload', 422

    endpoint_summaries = []
    with session_scope() as session:
        for endpoint in get_endpoints(session):
            endpoint_summary = make_endpoint_summary(endpoint, interval, baseline_interval)
            endpoint_summaries.append(endpoint_summary)

    return dict(summaries=endpoint_summaries)
