import unittest

from parsers.tg_channels import parse_channel_html
from selection import round_robin


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

        posts = parse_channel_html(html)

        self.assertEqual(posts, [("101", "First vacancy"), ("103", "Third vacancy")])


class SourceSelectionTests(unittest.TestCase):
    def test_round_robin_does_not_starve_later_sources(self):
        sources = [["fl-1", "fl-2", "fl-3"], ["kwork-1", "kwork-2"], ["tg-1", "tg-2"]]

        selected = list(round_robin(sources))[:5]

        self.assertEqual(selected, ["fl-1", "kwork-1", "tg-1", "fl-2", "kwork-2"])


if __name__ == "__main__":
    unittest.main()
