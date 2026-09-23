/// CONTRACT §4 Operator.
class RestInfo {
  const RestInfo({required this.status, this.nextAllowedStart, this.reason});

  final String status; // ok | warning | must_rest
  final String? nextAllowedStart;
  final String? reason;

  factory RestInfo.fromJson(Map<String, dynamic> j) => RestInfo(
        status: j['status'] as String,
        nextAllowedStart: j['next_allowed_start'] as String?,
        reason: j['reason'] as String?,
      );
}

class Operator {
  const Operator({
    required this.id,
    required this.name,
    required this.lang,
    required this.experience,
    required this.hoursToday,
    required this.hours7d,
    required this.rest,
  });

  final String id;
  final String name;
  final String lang;
  final Map<String, String> experience; // machineType -> Experience
  final double hoursToday;
  final double hours7d;
  final RestInfo rest;

  factory Operator.fromJson(Map<String, dynamic> j) => Operator(
        id: j['id'] as String,
        name: j['name'] as String,
        lang: j['lang'] as String,
        experience: (j['experience'] as Map)
            .map((k, v) => MapEntry(k as String, v as String)),
        hoursToday: (j['hours_today'] as num).toDouble(),
        hours7d: (j['hours_7d'] as num).toDouble(),
        rest: RestInfo.fromJson(j['rest'] as Map<String, dynamic>),
      );
}
