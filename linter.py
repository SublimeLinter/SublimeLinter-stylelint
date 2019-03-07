import json
import re
import logging
from SublimeLinter.lint import NodeLinter
from SublimeLinter.lint.linter import LintMatch

logger = logging.getLogger('SublimeLinter.plugin.stylelint')


class Stylelint(NodeLinter):

    npm_name = 'stylelint'
    cmd = 'stylelint --formatter json --stdin-filename ${file}'

    line_col_base = (1, 1)

    crash_regex = re.compile(
        r'^.*?\r?\n?\w*Error: (.*)',
        re.MULTILINE
    )

    defaults = {
        'selector': 'source.css - meta.attribute-with-value, source.sass, source.scss, source.less'  # noqa 501
    }

    def find_errors(self, output):
        """
        Parse errors from linter's output.

        We override this method to handle parsing stylelint crashes,
        deprecations and other feedback about the config.
        """
        data = None
        match = self.crash_regex.match(output)

        if match:
            msg = "Stylelint crashed: %s" % match.group(1)
            logger.warning(msg)
            self.notify_failure()

        try:
            if output and not match:
                data = json.loads(output)[0]
        except Exception as e:
            logger.warning(e)
            self.notify_failure()

        if data and 'invalidOptionWarnings' in data:
            if data['invalidOptionWarnings'] != []:
                self.notify_failure()
                for option in data['invalidOptionWarnings']:
                    text = option['text']
                    logger.warning(text)

        if data and 'deprecations' in data:
            if data['deprecations'] != []:
                self.notify_failure()
                for option in data['deprecations']:
                    text = option['text']
                    logger.warning(text)

        if data and 'warnings' in data:
            for warning in data['warnings']:
                line = warning['line'] - self.line_col_base[0]
                col = warning['column'] - self.line_col_base[1]
                text = warning['text'].replace('(' + warning['rule'] + ')', '')
                text = text.rstrip()

                yield LintMatch(
                    match=warning,
                    line=line,
                    col=col,
                    error_type=warning['severity'],
                    code=warning['rule'],
                    message=text
                )
