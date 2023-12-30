import os
import sys
from os.path import join as path_join
from asyncio import Event
from unittest.mock import AsyncMock

import httpx
import respx
import pytest

from wapitiCore.net.classes import CrawlerConfiguration
from wapitiCore.net import Request
from wapitiCore.net.crawler import AsyncCrawler
from wapitiCore.attack.mod_cms import ModuleCms


# Test no Drupal detected
@pytest.mark.asyncio
@respx.mock
async def test_no_drupal():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            text="<html><head><title>Vous Etes Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )

    # Response to check that we have no more false positives
    respx.get("http://perdu.com/core/misc/drupal.js").mock(return_value=httpx.Response(200))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert not persister.add_payload.call_count

@pytest.mark.asyncio
@respx.mock
async def test_drupal_version_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/drupal/")
    changelog_file = "CHANGELOG.txt"

    with open(path_join(test_directory, changelog_file), errors="ignore") as changelog:
        data = changelog.read()

    # Response to tell that Drupal is used
    respx.get("http://perdu.com/core/misc/drupal.js").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "application/javascript"})
    )

    # Response for changelog.txt
    respx.get("http://perdu.com/CHANGELOG.txt").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[0][1]["category"] == "Fingerprint web application framework"
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Drupal", "versions": ["7.67"], "categories": ["CMS Drupal"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[1][1]["category"] == "Fingerprint web technology"
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "Drupal", "versions": ["7.67"], "categories": ["CMS Drupal"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_drupal_multi_versions_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/drupal/")
    maintainers_file = "MAINTAINERS.txt"

    with open(path_join(test_directory, maintainers_file), errors="ignore") as maintainers:
        data = maintainers.read()

    # Response to tell that Drupal is used
    respx.get("http://perdu.com/core/misc/drupal.js").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "application/javascript"}
        )
    )

    # Response for  maintainers.txt
    respx.get("http://perdu.com/core/MAINTAINERS.txt").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Drupal", "versions": ["8.0.0-beta4", "8.0.0-beta5", "8.0.0-beta6"], "categories": ["CMS Drupal"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "Drupal", "versions": ["8.0.0-beta4", "8.0.0-beta5", "8.0.0-beta6"], "categories": ["CMS Drupal"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_drupal_version_not_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/drupal/")
    changelog_edited = "CHANGELOG_EDITED.txt"

    with open(path_join(test_directory, changelog_edited), errors="ignore") as changelog:
        data = changelog.read()

    # Response to tell that Drupal is used
    respx.get("http://perdu.com/misc/drupal.js").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Type": "application/javascript"}
        )
    )

    # Response for edited changelog.txt
    respx.get("http://perdu.com/CHANGELOG.txt").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Drupal", "versions": [], "categories": ["CMS Drupal"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_no_joomla():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            text="<html><head><title>Vous Etes Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )

    # Response to check that we have no more false positives

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert not persister.add_payload.call_count


@pytest.mark.asyncio
@respx.mock
async def test_joomla_version_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/joomla/")
    joomla_file = "joomla.xml"

    with open(path_join(test_directory, joomla_file), errors="ignore") as joomla:
        data = joomla.read()

    # Response to tell that Joomla is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head></head><body>This website use Joomla /administrator/ </body></html>")
    )

    # Response for joomla.xml
    respx.get("http://perdu.com/administrator/manifests/files/joomla.xml").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[0][1]["category"] == "Fingerprint web application framework"
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Joomla", "versions": ["3.10.12"], "categories": ["CMS Joomla"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[1][1]["category"] == "Fingerprint web technology"
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "Joomla", "versions": ["3.10.12"], "categories": ["CMS Joomla"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_joomla_multi_versions_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/joomla/")
    helpsite_file = "helpsite.js"

    with open(path_join(test_directory, helpsite_file), errors="ignore") as helpsite:
        data = helpsite.read()

    # Response to tell that Joomla is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head></head><body>This website use Joomla /administrator/ </body></html>")
    )

    # Response for  maintainers.txt
    respx.get("http://perdu.com/media/system/js/helpsite.js")\
        .mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["category"] == "Fingerprint web application framework"
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Joomla", "versions": ["3.3.4", "3.3.5", "3.3.6", "3.4.0-alpha"], "categories": ["CMS Joomla"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["category"] == "Fingerprint web technology"
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "Joomla", "versions": ["3.3.4", "3.3.5", "3.3.6", "3.4.0-alpha"], "categories": ["CMS Joomla"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_joomla_version_not_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/joomla/")
    joomla_edited = "joomla_edited.xml"

    with open(path_join(test_directory, joomla_edited), errors="ignore") as joomla:
        data = joomla.read()

    # Response to tell that Joomla is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head></head><body>This website use Joomla /administrator/ </body></html>")
    )

    # Response for edited changelog.txt
    respx.get("http://perdu.com/administrator/manifests/files/joomla.xml").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "Joomla", "versions": [], "categories": ["CMS Joomla"], "groups": ["Content"]}'
        )

@pytest.mark.asyncio
@respx.mock
async def test_no_prestashop():
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            text="<html><head><title>Vous Etes Perdu ?</title></head><body><h1>Perdu sur l'Internet ?</h1> \
            <h2>Pas de panique, on va vous aider</h2> \
            <strong><pre>    * <----- vous &ecirc;tes ici</pre></strong></body></html>"
        )
    )

    # Response to check that we have no more false positives

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert not persister.add_payload.call_count


@pytest.mark.asyncio
@respx.mock
async def test_prestashop_version_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/prestashop/")
    prestashop_file = "admin.js"

    with open(path_join(test_directory, prestashop_file), errors="ignore") as prestashop:
        data = prestashop.read()

    # Response to tell that PrestaShop is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="<html><head><title>Helo</title>\
            </head><body>This website uses Prestashop, prestashop = []</body></html>")
        )

    # Response for admin.js
    respx.get("http://perdu.com/js/admin.js")\
        .mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[0][1]["category"] == "Fingerprint web application framework"
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "PrestaShop", "versions": ["1.6.0.5"], "categories": ["CMS PrestaShop"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[1][1]["category"] == "Fingerprint web technology"
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "PrestaShop", "versions": ["1.6.0.5"], "categories": ["CMS PrestaShop"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_prestashop_multi_versions_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/prestashop/")
    helpsite_file = "theme.css"

    with open(path_join(test_directory, helpsite_file), errors="ignore") as helpsite:
        data = helpsite.read()

    # Response to tell that PrestaShop is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="This website use PrestaShop, prestashop = []")
    )

    # Response for  theme.css
    respx.get("http://perdu.com/themes/classic/assets/css/theme.css")\
        .mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "PrestaShop", "versions": ["1.7.7.6", "1.7.7.7", "1.7.7.8"], "categories": ["CMS PrestaShop"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "PrestaShop", "versions": ["1.7.7.6", "1.7.7.7", "1.7.7.8"], "categories": ["CMS PrestaShop"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_prestashop_version_not_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/prestashop/")
    prestashop_edited = "theme_edited.css"

    with open(path_join(test_directory, prestashop_edited), errors="ignore") as prestashop:
        data = prestashop.read()

    # Response to tell that PrestaShop is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="This website use Prestashop prestashop = []")
    )

    # Response for edited changelog.txt
    respx.get("http://perdu.com/themes/classic/assets/css/theme.css").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "PrestaShop", "versions": [], "categories": ["CMS PrestaShop"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_spip_version_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/spip/")
    spip_file = "CHANGELOG.txt"

    with open(path_join(test_directory, spip_file), errors="ignore") as spip:
        data = spip.read()

    # Response to tell that SPIP is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="This website use SPIP, your_spip_attribute = ''",
            headers={"composed-by": "SPIP"})
    )

    # Response for CHANGELOG.txt
    respx.get("http://perdu.com/CHANGELOG.txt").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[0][1]["category"] == "Fingerprint web application framework"
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "SPIP", "versions": ["v3.1.14"], "categories": ["CMS SPIP"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["module"] == "cms"
        assert persister.add_payload.call_args_list[1][1]["category"] == "Fingerprint web technology"
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "SPIP", "versions": ["v3.1.14"], "categories": ["CMS SPIP"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_prestashop_multi_versions_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/spip/")
    ajax_file = "ajaxCallback.js"

    with open(path_join(test_directory, ajax_file), errors="ignore") as ajax:
        data = ajax.read()

    # Response to tell that SPIP is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="This website use SPIP, your_spip_attribute = ''",
            headers={"composed-by": "SPIP"})
    )

    # Response for ajaxCallback.js
    respx.get("http://perdu.com/prive/javascript/ajaxCallback.js")\
        .mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 2
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "SPIP", "versions": ["v2.0.0", "v2.0.1", "v2.0.2", "v2.0.3"], "categories": ["CMS SPIP"], "groups": ["Content"]}'
        )
        assert persister.add_payload.call_args_list[1][1]["info"] == (
            '{"name": "SPIP", "versions": ["v2.0.0", "v2.0.1", "v2.0.2", "v2.0.3"], "categories": ["CMS SPIP"], "groups": ["Content"]}'
        )


@pytest.mark.asyncio
@respx.mock
async def test_spip_version_not_detected():

    base_dir = os.path.dirname(sys.modules["wapitiCore"].__file__)
    test_directory = os.path.join(base_dir, "..", "tests/data/spip/")
    spip_edited = "CHANGELOG_edited.txt"

    with open(path_join(test_directory, spip_edited), errors="ignore") as spip:
        data = spip.read()

    # Response to tell that SPIP is used
    respx.get("http://perdu.com/").mock(
        return_value=httpx.Response(
            200,
            content="This website use SPIP, your_spip_attribute = ''",
            headers={"composed-by": "SPIP"})
    )

    # Response for edited changelog.txt
    respx.get("http://perdu.com/CHANGELOG.txt").mock(return_value=httpx.Response(200, text=data))

    respx.get(url__regex=r"http://perdu.com/.*?").mock(return_value=httpx.Response(404))

    persister = AsyncMock()

    request = Request("http://perdu.com/")
    request.path_id = 1

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"))
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2, "tasks": 20}

        module = ModuleCms(crawler, persister, options, Event(), crawler_configuration)

        await module.attack(request)

        assert persister.add_payload.call_count == 1
        assert persister.add_payload.call_args_list[0][1]["info"] == (
            '{"name": "SPIP", "versions": [], "categories": ["CMS SPIP"], "groups": ["Content"]}'
        )
