import os
import json
import time
import numpy as np
from lxml.html import html5parser, tostring
from lxml.html.clean import Cleaner
import html5lib
# from threading import Thread

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options


import PIL

import ipdb


class MiniWoBInstance:
    """
    Interface to interact with a selenium broswer instance
    """

    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 240
    TASK_WIDTH = 160
    TASK_HEIGHT = 210

    def __init__(
            self, task_file,
            base_url= 'https://www.github.com/',
            # base_url= 'http://127.0.0.1:8080/miniwob/book-flight.html', # os.getenv("WOB_PATH"),
            wait_ms=0., block_on_reset=True, refresh_freq=0
            ):
        """
        E.g. base_url='file:///h/sheng/DOM-Q-NET/miniwob/html/miniwob/',
        Args:
            wait_ms: pause the instance after each action for this ms
            block_on_reset: On reset, block until the page loads
            refresh_freq: Every this # episodes, refresh the page at the begin
                          of the next episode
        http://guppy7:8000/miniwob/
        """
        super(MiniWoBInstance, self).__init__()
        print("Opening MiniWoB")

        url = base_url  # + task_file
        options = webdriver.FirefoxOptions()
        # options.set_headless()
        options.add_argument('-safe-mode')
        self._driver = webdriver.Firefox(options=options)
        self._driver.get(url)
        print("Firefox Task title: " + self._driver.title)

        #NOTE Chrome driver
        # url = base_url + task_file
        # chrome_options = Options()
        # chrome_options.add_argument("--headless")
        # self._url = url
        # self._driver = webdriver.Chrome(chrome_options=chrome_options)
        # self._driver.get(url)
        # print("Chrome Task title: " + self._driver.title)

        self._state = dict()
        self._state_tree = None
        self._meta = {
            'done': False,
            'env_reward': 0,
            'raw_reward': 1,
            'info': 'no reason'
        }
        self._current_url = ''
        self._pre_dom_num = 0

    def __del__(self):
        print("Closing MiniWoB")
        self._driver.quit()
        # self._driver.close()

    @property
    def utterance(self):
        # return self._driver.execute_script('return core.getUtterance();')
        return "Someting We may care should be put into here, likes: Books, Sports, Android"

    @property
    def dom(self):
        # dom_html = self._driver.execute_script('return core.getDOMInfo();')

        # try:
        #     print('get the dom of the instance!')
        #     dom_str = self._driver.execute_script('return document.body.outerHTML')
        #     # dom_str = self.get_dom_str()
        # except Exception as ex:
        #     print('dom is not ready yet, error:', ex)
        #     dom_str = '<body></body>'
        # # print(dom_str)

        # # dom_str = clean_dom(dom_str)
        # # print(dom_str)
        # dom_tree = html5lib.parse(dom_str, treebuilder='lxml', namespaceHTMLElements=False)
        # # dom_tree = html5parser.fromstring(dom_str)
        # self._state_tree = dom_tree
        # dom_tree = dom_tree.getroot()
        # # print(tostring(dom_tree))

        # dom_tree = self.add_dom_ref_attribute(dom_tree)
        # dom_tree = self.add_dom_attributes(dom_tree)
        #print(tostring(mini_dom))

        # mini_dom = get_dom_of_element(dom_tree)
        mini_dom = {
            'tag': 'body',
            'id': '',
            'classes': '',
            'ref': 0,
            'top': 0,
            'left': 0,
            'weight': 0,
            'height': 0,
            'children': []
        }
        try:
            web_dom = self.get_dom()
            if web_dom is not None:
                mini_dom = web_dom
            # print(mini_dom)
        except Exception as ex:
            print(f'fail to get dom, error:{ex}')
        # print(mini_dom)
        self.save_dom(mini_dom)
        self._pre_dom_num = len(self._state.keys())
        return mini_dom

    @property
    def reward_avg(self):
        # return self._driver.execute_script('return core.rewardAvg();')
        return 0

    @property
    def is_done(self):
        return self._driver.execute_script(
                'return {'
                '"done": false,'
                '};')

    @property
    def img(self):
        png_data = self._driver.get_screenshot_as_png()
        pil_img = PIL.Image.open(png_data)
        pil_img = pil_img.crop(
                (0, 0, self.TASK_WIDTH, self.TASK_HEIGHT)
                ).convert('RGB')
        return pil_img

    @property
    def metadata(self):
        # return self._driver.execute_script(
        #         'return {'
        #         '"done": false,'
        #         '"env_reward": 0,'
        #         '"raw_reward": 1,'
        #         '"info": "no reason",'
        #         '};')

        return self._meta

    def begin_task(self, seed=None):
        """
        args:
            seed: e.g. 'hello', 'itsme',
        """
        seed=None
        if seed is not None:
            self._driver.execute_script('Math.seedrandom({});'.format(repr(seed)))
        # print(self._driver.execute_script('return WOB_TASK_READY;') )
        # self._driver.execute_script('core.startEpisodeReal();')

    def force_stop(self):
        pass
        # self._driver.execute_script('return core.endEpisode(0);')

    def terminate(self):
        pass
        # self._driver.execute_script('return core.endEpisode(-1, false, "terminate");')

    def coord_click(self, left, top):
        body = self._driver.find_element_by_tag_name('body')
        chain = ActionChains(self._driver)
        chain.move_to_element_with_offset(body, left, top).click().perform()

    def dom_click(self, ref, fail_hard=False):
        self._meta['raw_reward'] = 0
        if ref in self._state.keys():
            tree_element = self._state[ref]
        else:
            print(f'selected dom is not existed, ref={ref}')
            return

        print(f'click dom element, ref:{ref}')
        print(f'click dom: {tree_element}')

        result = None

        # try:
        #     if tree_element.get('id') is not None:
        #         element = self._driver.find_element_by_id(tree_element.get('id'))
        #     else:
        #         element = self._driver.find_element_by_xpath(self._state_tree.getpath(tree_element))

        #     self._driver.execute_script("arguments[0].scrollIntoView();", element);
        #     ActionChains(self._driver).move_to_element(element).click().perform()
        # except Exception as ex:
        #     print(f'can not click the target element! err: {ex}')

        try:
            click_script = '''
                window.canvasDrawElementClick = function (element) {
                    // if (!window.prepareCanvas()) return;
                    // var rect = element.getBoundingClientRect()
                    // var ctx = core.clickTrackCtx;
                    // ctx.fillStyle = "rgba(100, 100, 255, 0.8)";
                    // ctx.fillRect(rect.left, rect.top, rect.width, rect.height);
                }

                window.elementClick = function (ref) {
                    try {
                        var element = window.previousDOMInfo[ref];
                        window.canvasDrawElementClick(element);
                        if (element instanceof SVGElement) {
                            // SVG needs special treatment
                            var event = new Event('mousedown');
                            element.dispatchEvent(event);
                            var event = new Event('mouseup');
                            element.dispatchEvent(event);
                            var event = new Event('click');
                            element.dispatchEvent(event);
                        } else {
                            element.click();
                            element.focus();
                        }
                        return true;
                    } catch (err) {
                        return err.message;
                    }
                }
            '''
            self._driver.execute_script(click_script)
            self._driver.execute_script(
                    'return window.elementClick({});'.format(ref)
                    )
            if self._current_url != self._driver.current_url:
                self._current_url = self._driver.current_url
                self._meta['raw_reward'] = 1
            else:
                self._meta['raw_reward'] = 0

                if self._pre_dom_num != len(self._state.keys()):
                    self._meta['raw_reward'] = 1
                    self._pre_dom_num = len(self._state.keys())

        except Exception as ex:
            print(f'fail to click element, error:{ex}')
            return

        # if not result:
        #     if fail_hard:
        #         raise RuntimeError()
        #     else:
        #         pass

    def type(self, text):
        # TODO WHY WOULD CLICK PAD TOKEN????
        chain = ActionChains(self._driver)
        chain.send_keys(text)
        chain.perform()
        if text == "<pad>":
            ipdb.set_trace()

    def focus_and_type(self, ref, text):
        self.dom_click(ref)
        self.type(text)

    def save_dom(self, dom):
        if 'ref' not in dom.keys():
            return

        self._state[dom['ref']] = dom

        for child in dom['children']:
            self.save_dom(child)

    def add_dom_ref_attribute(self, dom_tree):
        self._state = dict()
        ref = 0
        self._state[ref] = dom_tree

        for child in dom_tree.iter():
            try:
                ref += 1
                child.set('ref', str(ref))

                self._state[ref] = child
            except:
                # print(f'immutable element, ignore it - {child.tag}')
                # parent = child.getparent()
                # parent.remove(child)
                pass

        return dom_tree

    def add_dom_attributes(self, dom_tree):

        for child in dom_tree.iter():
            try:
                path = self._state_tree.getpath(child)
                element = self._driver.find_element_by_xpath(path)
                location = element.location
                size = element.size
                # print(f'size: {size}, location: {location}')
                # if size['width'] > 0.0 or size['height'] > 0.0:
                child.set('width', str(size['width']))
                child.set('height', str(size['height']))
                child.set('top', str(location['y']))
                child.set('left', str(location['x']))

            except Exception as ex:
                # print(f'can not get the element, ignore it - {path}, err - {ex}')
                pass

        return dom_tree

    def get_dom(self):
        dom_script = '''
            var core = {};
            window.nextRefCode = 0;
            window.previousDOMInfo = {};

            window.canvasDrawElementClick = function (element) {
                // if (!window.prepareCanvas()) return;
                // var rect = element.getBoundingClientRect()
                // var ctx = core.clickTrackCtx;
                // ctx.fillStyle = "rgba(100, 100, 255, 0.8)";
                // ctx.fillRect(rect.left, rect.top, rect.width, rect.height);
            }

            window.elementClick = function (ref) {
                try {
                    var element = window.previousDOMInfo[ref];
                    window.canvasDrawElementClick(element);
                    if (element instanceof SVGElement) {
                        // SVG needs special treatment
                        var event = new Event('mousedown');
                        element.dispatchEvent(event);
                        var event = new Event('mouseup');
                        element.dispatchEvent(event);
                        var event = new Event('click');
                        element.dispatchEvent(event);
                    } else {
                        element.click();
                        element.focus();
                    }
                    return true;
                } catch (err) {
                    return err.message;
                }
            }

            window.getDOMInfo = function (baseElement) {

                function getDOMInfoOfElement(element) {
                    var rect = element.getBoundingClientRect();
                    if (rect.width == 0 && rect.height == 0) return;
                    var answer = {
                        tag: element.tagName,
                        left: rect.left, top: rect.top,
                        width: rect.width, height: rect.height,
                        children: [],
                        id: element.id,
                        classes: element.className.toString(),
                    };
                    // Assign ref code
                    if (element.dataset.wob_ref !== undefined &&
                        element.dataset.wob_eps === 'e') {
                        answer.ref = +element.dataset.wob_ref;
                    } else {
                        element.dataset.wob_ref = answer.ref = window.nextRefCode++;
                        // element.dataset.wob_eps = 'e' + window.WOB_EPISODE_ID;
                    }
                    // Record styles
                    var computedStyle = window.getComputedStyle(element);
                    answer.bgColor = computedStyle.backgroundColor;
                    answer.fgColor = computedStyle.color;
                    // Indicate if the element is being focused on
                    if (document.activeElement === element) {

                    }
                    // Indicate if the element is tampered with in this episode
                    if (element.dataset.tampered !== undefined &&
                        element.dataset.tampered == 'e') {
                        answer.tampered = true;
                    }
                    // For recording demonstrations: Record the target
                    if (element.dataset.recording_target) {
                    answer.recordingTarget = true;
                    }
                    // For <input>, also add input type and value
                    if (element instanceof HTMLInputElement) {
                    var inputType = element.type;
                    answer.tag += '_' + inputType;
                    if (inputType === 'checkbox' || inputType === 'radio') {
                        answer.value = element.checked;
                    } else {
                        answer.value = element.value;
                    }
                    } else if (element instanceof HTMLTextAreaElement) {
                    answer.value = element.value;
                    }
                    window.previousDOMInfo[answer.ref] = element;

                    // Truncate too many dom nodes
                    if (answer.ref > 800) {
                        return answer;
                    }

                    // Read the children
                    var filteredChildNodes = [], textOnly = true;
                    element.childNodes.forEach(function (child) {
                    if (child instanceof Text) {
                        if (!/^\s*$/.test(child.data)) {
                        filteredChildNodes.push(child);
                        }
                    } else if (child instanceof Element) {
                        filteredChildNodes.push(child);
                        textOnly = false;
                    }
                    });
                    if (textOnly) {
                    answer.text = filteredChildNodes.map(function (x) {
                        return x.data.trim();
                    }).join(' ');
                    } else {
                    filteredChildNodes.forEach(function (child) {
                        if (child instanceof Text) {
                        addDOMInfosOfTextNode(child, answer.children);
                        } else {
                        child = getDOMInfoOfElement(child);
                        if (child !== undefined)
                            answer.children.push(child);
                        }
                    });
                    }
                    return answer;
                }

                function addDOMInfosOfTextNode(textNode, collection) {
                    // Break the text node into multiple nodes
                    // Each node only occupies a single rectangle boundary
                    var range = document.createRange();
                    range.selectNodeContents(textNode);
                    var absolute_start = range.startOffset, absolute_end = range.endOffset;
                    var start = absolute_start;
                    var itr = 0;
                    while (start < absolute_end) {
                    // Binary search on the next end point
                    var end_lower_bound = start + 1,
                        end_upper_bound = absolute_end,
                        l = range.getClientRects().length,
                        end = Math.floor((end_lower_bound * (l-1) + end_upper_bound) / l);
                    while (end_lower_bound <= end_upper_bound) {
                        range.setEnd(textNode, end);
                        if (range.getClientRects().length == 1) {
                        end_lower_bound = end + 1;
                        end = Math.min(end_lower_bound + 5, Math.floor((end_lower_bound + end_upper_bound) / 2));
                        } else {
                        end_upper_bound = end - 1;
                        end = Math.max(end_upper_bound - 5, Math.floor((end_lower_bound + end_upper_bound) / 2));
                        }
                        if (itr++ > 1000) throwTextNodeError('Text node computation stuck in an infinite loop');
                    }
                    range.setEnd(textNode, end);
                    var rects = range.getClientRects();
                    if (rects.length !== 1) throwTextNodeError('Text node computation incorrect');
                    var rect = rects[0], text = textNode.data.substring(start, end).trim();
                    if (rect.width > 0 && rect.height > 0 && text) {
                        var answer = {
                        tag: "t",
                        left: rect.left, top: rect.top,
                        width: rect.width, height: rect.height,
                        ref: window.nextTextRefCode--,
                        children: [],
                        text: text,
                        };
                        collection.push(answer);
                    }
                    start = end;
                    range.setEnd(textNode, absolute_end);
                    range.setStart(textNode, start);
                    if (itr++ > 1000) throwTextNodeError('Text node computation stuck in an infinite loop');
                    }
                }

                function throwTextNodeError(message) {
                    alert(message);
                    throw message;
                }

                return getDOMInfoOfElement(baseElement || document.body);
            }

            return window.getDOMInfo();
        '''

        return self._driver.execute_script(dom_script)


def clean_dom(dom_html):
    cleaner = Cleaner(style=True, links=True, add_nofollow=True,
                        page_structure=False, safe_attrs_only=False)

    return cleaner.clean_html(dom_html)


def get_dom_of_element(elem):
    state_dom = dict()
    ref_val = elem.get('ref')
    if ref_val is None:
        ref_val = '901'

    state_dom['tag'] = elem.tag
    state_dom['top'] = elem.get('top')
    state_dom['left'] = elem.get('left')
    state_dom['height'] = elem.get('height')
    state_dom['width'] = elem.get('width')
    state_dom['id'] = elem.get('id')
    state_dom['classes'] = elem.get('class')
    state_dom['ref'] = int(ref_val)
    state_dom['value'] = elem.get('value')
    state_dom['children'] = []

    if state_dom['ref'] > 850:
        return state_dom

    for child in elem.iterchildren():
        child_dom = get_dom_of_element(child)
        state_dom['children'].append(child_dom)

    return state_dom


if __name__ == '__main__':
    pass

