import unittest

from parsers.tg_channels import orders_from_post, parse_channel_html, split_vacancies


class TelegramParserTests(unittest.TestCase):
    def test_text_is_paired_with_id_from_same_message(self):
        html = """
        <div class="tgme_widget_message" data-post="jobs/101">
          <div class="tgme_widget_message_text js-message_text">First vacancy</div>
        </div>
        <div class="tgme_widget_message" data-post="jobs/102">
          <a class="tgme_widget_message_photo_wrap"></a>
        </div>
        <div class="tgme_widget_message" data-post="jobs/103">
          <div class="tgme_widget_message_text js-message_text">Third vacancy</div>
        </div>
        """
        self.assertEqual(parse_channel_html(html), [("101", "First vacancy"), ("103", "Third vacancy")])

    def test_preserves_line_breaks_from_telegram_html(self):
        html = """
        <div class="tgme_widget_message" data-post="frilans/357">
          <div class="tgme_widget_message_text js-message_text">
            #Дизайнер<br>Нарисовать логотип<br>➡️ @first<br>#SMM<br>Вести канал<br>➡️ @second
          </div>
        </div>
        """
        self.assertEqual(
            parse_channel_html(html),
            [("357", "#Дизайнер\nНарисовать логотип\n➡️ @first\n#SMM\nВести канал\n➡️ @second")],
        )

    def test_splits_digest_after_contact_before_next_role(self):
        text = (
            "#Дизайнер\nНарисовать логотип и фирменный стиль\n➡️ @first\n"
            "#SMM\nВести Telegram канал и готовить контент\n➡️ @second"
        )
        self.assertEqual(
            split_vacancies(text),
            [
                "#Дизайнер\nНарисовать логотип и фирменный стиль\n➡️ @first",
                "#SMM\nВести Telegram канал и готовить контент\n➡️ @second",
            ],
        )

    def test_keeps_consecutive_role_hashtags_in_one_vacancy(self):
        text = "#Сценарист\n#контентменеджер\nИщем специалиста в мебельную нишу\n➡️ @contact"
        self.assertEqual(split_vacancies(text), [text])

    def test_digest_parts_get_stable_unique_ids(self):
        text = "#Дизайнер\nЗадача первая\n➡️ @first\n#SMM\nЗадача вторая\n➡️ @second"
        orders = orders_from_post("frilans", "357", text)
        self.assertEqual([order.id for order in orders], ["tg_frilans_357_1", "tg_frilans_357_2"])
        self.assertEqual([order.url for order in orders], ["https://t.me/frilans/357"] * 2)


if __name__ == "__main__":
    unittest.main()
