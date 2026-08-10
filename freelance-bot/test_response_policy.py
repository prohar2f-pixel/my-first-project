import importlib
import importlib.util
import unittest


def load_policy():
    if importlib.util.find_spec("response_policy") is None:
        raise AssertionError(
            "response_policy.py is missing; Task 3 must implement the tested contract"
        )
    return importlib.import_module("response_policy")


class VerifiedFactsTests(unittest.TestCase):
    def test_verified_capabilities_do_not_claim_tilda_or_wordpress(self):
        policy = load_policy()

        capabilities = " ".join(policy.VERIFIED_CAPABILITIES).lower()

        self.assertIn("собствен", capabilities)
        self.assertIn("html", capabilities)
        self.assertNotIn("tilda", capabilities)
        self.assertNotIn("тильд", capabilities)
        self.assertNotIn("wordpress", capabilities)
        self.assertNotIn("вордпресс", capabilities)

    def test_salon_01_is_a_concept_not_client_work(self):
        policy = load_policy()

        salon = next(
            project for project in policy.DEMO_PROJECTS
            if project["name"] == "SALON 01"
        )

        self.assertEqual(salon["kind"], "concept")
        self.assertFalse(salon["is_client_work"])
        self.assertIsNone(salon["public_url"])

    def test_confirmed_public_destinations_pass_link_validation(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            (
                "Портфолио: https://aiprohar.ru/ "
                "Проект: https://nedvizhimostdoneck.ru/ "
                "Telegram: https://t.me/alex_prohar"
            ),
            risks=(),
        )

        self.assertNotIn("unsupported_claim:unknown_link", violations)


class RiskAssessmentTests(unittest.TestCase):
    def test_tilda_requirement_is_flagged_as_unverified_platform(self):
        policy = load_policy()

        risks = policy.assess_job_risks(
            "Перенос лендинга",
            "Нужен разработчик с коммерческим опытом работы в Tilda Zero Block.",
        )

        self.assertIn("unverified_platform:tilda", risks)

    def test_wordpress_requirement_is_flagged_as_unverified_platform(self):
        policy = load_policy()

        risks = policy.assess_job_risks(
            "Поддержка сайта",
            "Ищем WordPress-разработчика для Elementor и WooCommerce.",
        )

        self.assertIn("unverified_platform:wordpress", risks)

    def test_exact_estimate_is_unsafe_when_scope_is_missing(self):
        policy = load_policy()

        risks = policy.assess_job_risks(
            "Сверстать сайт",
            "Назовите точную цену и срок. Нужен современный сайт примерно на 20 страниц.",
        )

        self.assertIn("missing_scope:layouts", risks)
        self.assertIn("missing_scope:unique_pages", risks)
        self.assertIn("missing_scope:integrations", risks)
        self.assertIn("exact_estimate:unsafe", risks)

    def test_scoped_custom_code_job_has_no_platform_or_estimate_risk(self):
        policy = load_policy()

        risks = policy.assess_job_risks(
            "Адаптивная HTML-вёрстка по Figma",
            (
                "Три уникальные страницы. Макеты: https://figma.com/file/demo. "
                "Нужны HTML, CSS и JavaScript, форма отправляет заявку в Telegram. "
                "Срок обсуждаем после просмотра макетов."
            ),
        )

        self.assertFalse(any(risk.startswith("unverified_platform:") for risk in risks))
        self.assertNotIn("missing_scope:unique_pages", risks)
        self.assertNotIn("missing_scope:layouts", risks)
        self.assertNotIn("missing_scope:integrations", risks)
        self.assertNotIn("exact_estimate:unsafe", risks)


class GeneratedResponseValidationTests(unittest.TestCase):
    def test_blocks_claimed_tilda_experience(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            "Работаю с Tilda пять лет и сделал много коммерческих проектов.",
            risks=("unverified_platform:tilda",),
        )

        self.assertIn("unsupported_claim:platform_experience", violations)

    def test_blocks_presenting_salon_01_as_client_work(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            "Для клиента SALON 01 я разработал сайт салона под ключ.",
            risks=(),
        )

        self.assertIn("unsupported_claim:concept_as_client", violations)

    def test_blocks_unverified_measurable_result(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            "После моей работы конверсия выросла на 40% за месяц.",
            risks=(),
        )

        self.assertIn("unsupported_claim:metric", violations)

    def test_blocks_exact_price_and_deadline_for_incomplete_scope(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            "Сделаю весь проект за 25 000 рублей ровно за 7 дней.",
            risks=("exact_estimate:unsafe",),
        )

        self.assertIn("unsupported_claim:exact_estimate", violations)

    def test_blocks_unknown_link(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            "Примеры моих работ: https://example-fake-portfolio.test/cases",
            risks=(),
        )

        self.assertIn("unsupported_claim:unknown_link", violations)

    def test_blocks_unconfirmed_path_on_known_domain(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            "Кейс: https://aiprohar.ru/cases/not-confirmed/",
            risks=(),
        )

        self.assertIn("unsupported_claim:unknown_link", violations)

    def test_malformed_url_fails_closed_without_crashing(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            "Кейс: https://aiprohar.ru:not-a-port/",
            risks=(),
        )

        self.assertIn("unsupported_claim:unknown_link", violations)

    def test_allows_honest_response_with_confirmed_link(self):
        policy = load_policy()

        violations = policy.validate_generated_response(
            (
                "Основной подтверждённый опыт у меня в разработке сайтов "
                "собственным кодом. Портфолио: https://aiprohar.ru/ "
                "Точную оценку дам после просмотра макетов и интеграций."
            ),
            risks=("unverified_platform:tilda", "exact_estimate:unsafe"),
        )

        self.assertEqual(violations, ())


class SafeFallbackTests(unittest.TestCase):
    def test_platform_fallback_declines_unverified_platform_and_offers_alternative(self):
        policy = load_policy()

        result = policy.build_safe_fallback(
            risks=("unverified_platform:wordpress",),
            job_title="WordPress-разработчик",
            job_description="Нужна поддержка сайта на Elementor.",
        )

        text = result.text.lower()
        self.assertTrue(result.fallback)
        self.assertIn("нет", text)
        self.assertIn("подтвержд", text)
        self.assertIn("собствен", text)
        self.assertIn("если принципиаль", text)
        self.assertIn("https://aiprohar.ru/", text)

    def test_generic_fallback_keeps_verified_custom_code_pitch(self):
        policy = load_policy()

        result = policy.build_safe_fallback(
            risks=("missing_scope:layouts", "exact_estimate:unsafe"),
            job_title="Адаптивная вёрстка",
            job_description="Нужно сверстать новый сайт, подробности позже.",
        )

        text = result.text.lower()
        self.assertTrue(result.fallback)
        self.assertIn("адаптив", text)
        self.assertIn("собствен", text)
        self.assertIn("точную стоимость", text)
        self.assertNotIn("этот заказ мне не подходит", text)


if __name__ == "__main__":
    unittest.main()
