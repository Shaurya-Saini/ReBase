/// CONTRACT §4 Estimate (XGBoost, backend).
class EstimateFactor {
  const EstimateFactor(
      {required this.name, required this.effectPct, this.note});

  final String name;
  final num effectPct; // signed % effect on the estimate
  final String? note;

  factory EstimateFactor.fromJson(Map<String, dynamic> j) => EstimateFactor(
        name: j['name'] as String,
        effectPct: j['effect_pct'] as num,
        note: j['note'] as String?,
      );
}

class Estimate {
  const Estimate({
    required this.jobId,
    required this.estimatedHours,
    required this.rangeHours,
    required this.factors,
    this.projectCompletionDate,
  });

  final String jobId;
  final double estimatedHours;
  final List<double> rangeHours; // [low, high]
  final List<EstimateFactor> factors;
  final String? projectCompletionDate;

  factory Estimate.fromJson(Map<String, dynamic> j) => Estimate(
        jobId: j['job_id'] as String,
        estimatedHours: (j['estimated_hours'] as num).toDouble(),
        rangeHours: (j['range_hours'] as List)
            .map((e) => (e as num).toDouble())
            .toList(),
        factors: (j['factors'] as List)
            .map((e) => EstimateFactor.fromJson(e as Map<String, dynamic>))
            .toList(),
        projectCompletionDate: j['project_completion_date'] as String?,
      );
}
