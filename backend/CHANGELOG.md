# Changelog

## [0.2.0](https://github.com/jkuwalek/dmv-reservation-scheduler/compare/dmvwatch-v0.1.0...dmvwatch-v0.2.0) (2026-11-19)


### Features

* add alembic migrations ([3495bef](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/3495beffcec0c3a37bbac0c0cb64729ff1f2e9fe))
* add console and resend notifiers ([5d240be](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/5d240be8a8d76b07820e063e42da9244196f6c31))
* add crawl policy and per-host throttle ([93e16f1](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/93e16f1b159b3e9a645462028e518b14db0329b9))
* add database schema ([b73086d](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/b73086d1e5ab4ae81bb8eb64763fdeaeae8cbcf2))
* add enrolment service with confirm and booked handling ([f542ed5](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/f542ed57f52968435f75aa284c3588db1d4855bf))
* add http api for enrolment and action links ([707c906](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/707c9063526bbc8c7633600d446500045d65e83a))
* add office, slot and transaction type models ([3bfffbb](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/3bfffbbf1faaf82d4229a7d7e39b4e1a6cd31502))
* add postgres observation repository ([084483e](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/084483e71e71039ed18d7aa7879ebb05efc930a0))
* add postgres watch repository ([3604f70](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/3604f703aa3c0550f4f2634d6d83317fdcc3061d))
* add settings and local service definitions ([03370e5](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/03370e57c6ebaf858b55681e80cf5fb779516c57))
* add signed one-click action links ([b9ac9e3](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/b9ac9e3e275d847adc22d92dcfc034755c056ad5))
* add state adapter registry ([3597017](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/3597017d597a3b1c6ef71f8eea7bc8532cb28a49))
* add sweep service that records observations and detects new slots ([b5321bb](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/b5321bbbf22047ed9ff5b6a2dc38bb0889eed7b1))
* add watch status and sweep result ([40899d7](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/40899d79a6f87c2753bf3f180a4c8c8573c850fc))
* add worker task that sweeps every office ([ad50bd0](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/ad50bd0ac5b394863f2b6e96b2ab5b6895ba4d83))
* define clock and slot source protocols ([4dde543](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/4dde543f6dc55680bd7cbcbbdb51ee68cb5b9693))
* define enrolment protocols ([e5a55f5](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/e5a55f55fe1fe6edeb54a1f6323f44aa8dbf9c78))
* encrypt access codes and keep them out of logs ([255602f](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/255602f9e99bae088ec956b90b2e7703b1d75b76))
* validate scraped slots before use ([d182792](https://github.com/jkuwalek/dmv-reservation-scheduler/commit/d182792192cf5bc95b9f270eef24379e8485c878))
