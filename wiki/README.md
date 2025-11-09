# Enterprise GuardCAP (MASKIT) - Wiki Documentation

기업용 DLP (Data Loss Prevention) 솔루션 **MASKIT**의 공식 문서입니다.


## 문서 구성

이 위키에는 다음과 같은 문서들이 포함되어 있습니다:

1. **[Overview](index.md)** - MASKIT 서비스 개요 및 주요 기능
2. **[설치 및 사용법](2_install.md)** - 시스템 설치 및 역할별 사용 가이드
3. **[Analyzer](3_analyzer.md)** - PII 분석 엔진 설명
4. **[기술 스택](4_techstack.md)** - 사용된 기술 스택 및 시스템 아키텍처
5. **[PII Entities](5_PII_entities.md)** - 탐지 가능한 개인정보 엔티티 목록
6. **[LLM](6_LLM.md)** - LLM/RAG 기반 정책 관리 시스템
7. **[Redactor](7_redactor.md)** - 마스킹 및 익명화 엔진
8. **[FastAPI](8_fastapi.md)** - 백엔드 API 문서
9. **[User Interface](9_userinterface.md)** - 프론트엔드 UI 가이드
10. **[Mail Proxy](10_mailproxy.md)** - SMTP 프록시 서버 구조
11. **[Solution DLP](11_solutionDLP.md)** - DLP 솔루션 통합 가이드

## 빠른 시작

MASKIT을 처음 사용하시나요? 다음 문서들을 순서대로 읽어보세요:

1. [서비스 개요](index.md) - MASKIT이 무엇인지 이해하기
2. [설치 및 사용법](2_install.md) - 시스템 설치 및 첫 로그인
3. [기술 스택](4_techstack.md) - 시스템 아키텍처 이해하기

## 로컬에서 Wiki 실행하기

이 위키를 로컬에서 실행하려면:

After completing the creation of your new site on GitHub, update it as needed:

## Replace the content of the template pages

Update the following files to your own content:

- `index.md` (your new home page)
- `README.md` (information for those who access your site repo on GitHub)

## Changing the version of the theme and/or Jekyll

Simply edit the relevant line(s) in the `Gemfile`.

## Adding a plugin

The Just the Docs theme automatically includes the [`jekyll-seo-tag`] plugin.

To add an extra plugin, you need to add it in the `Gemfile` *and* in `_config.yml`. For example, to add [`jekyll-default-layout`]:

- Add the following to your site's `Gemfile`:

  ```ruby
  gem "jekyll-default-layout"
  ```

- And add the following to your site's `_config.yml`:

  ```yaml
  plugins:
    - jekyll-default-layout
  ```

Note: If you are using a Jekyll version less than 3.5.0, use the `gems` key instead of `plugins`.

## Publishing your site on GitHub Pages

1.  If your created site is `YOUR-USERNAME/YOUR-SITE-NAME`, update `_config.yml` to:

    ```yaml
    title: YOUR TITLE
    description: YOUR DESCRIPTION
    theme: just-the-docs

    url: https://YOUR-USERNAME.github.io/YOUR-SITE-NAME

    aux_links: # remove if you don't want this link to appear on your pages
      Template Repository: https://github.com/YOUR-USERNAME/YOUR-SITE-NAME
    ```

2.  Push your updated `_config.yml` to your site on GitHub.

3.  In your newly created repo on GitHub:
    - go to the `Settings` tab -> `Pages` -> `Build and deployment`, then select `Source`: `GitHub Actions`.
    - if there were any failed Actions, go to the `Actions` tab and click on `Re-run jobs`.

## Building and previewing your site locally

Assuming [Jekyll] and [Bundler] are installed on your computer:

1.  Change your working directory to the root directory of your site.

2.  Run `bundle install`.

3.  Run `bundle exec jekyll serve` to build your site and preview it at `localhost:4000`.

    The built site is stored in the directory `_site`.

## Publishing your built site on a different platform

Just upload all the files in the directory `_site`.

## Customization

You're free to customize sites that you create with this template, however you like!

[Browse our documentation][Just the Docs] to learn more about how to use this theme.

## Hosting your docs from an existing project repo

You might want to maintain your docs in an existing project repo. Instead of creating a new repo using the [just-the-docs template](https://github.com/just-the-docs/just-the-docs-template), you can copy the template files into your existing repo and configure the template's Github Actions workflow to build from a `docs` directory. You can clone the template to your local machine or download the `.zip` file to access the files.

### Copy the template files

1.  Create a `.github/workflows` directory at your project root if your repo doesn't already have one. Copy the `pages.yml` file into this directory. GitHub Actions searches this directory for workflow files.

2.  Create a `docs` directory at your project root and copy all remaining template files into this directory.

### Modify the GitHub Actions workflow

The GitHub Actions workflow that builds and deploys your site to Github Pages is defined by the `pages.yml` file. You'll need to edit this file to that so that your build and deploy steps look to your `docs` directory, rather than the project root.

1.  Set the default `working-directory` param for the build job.

    ```yaml
    build:
      runs-on: ubuntu-latest
      defaults:
        run:
          working-directory: docs
    ```

2.  Set the `working-directory` param for the Setup Ruby step.

    ```yaml
    - name: Setup Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'
          bundler-cache: true
          cache-version: 0
          working-directory: '${{ github.workspace }}/docs'
    ```

3.  Set the path param for the Upload artifact step:

    ```yaml
    - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/_site/
    ```

4.  Modify the trigger so that only changes within the `docs` directory start the workflow. Otherwise, every change to your project (even those that don't affect the docs) would trigger a new site build and deploy.

    ```yaml
    on:
      push:
        branches:
          - "main"
        paths:
          - "docs/**"
    ```

## Licensing and Attribution

This repository is licensed under the [MIT License]. You are generally free to reuse or extend upon this code as you see fit; just include the original copy of the license (which is preserved when you "make a template"). While it's not necessary, we'd love to hear from you if you do use this template, and how we can improve it for future use!

The deployment GitHub Actions workflow is heavily based on GitHub's mixed-party [starter workflows]. A copy of their MIT License is available in [actions/starter-workflows].

----

[^1]: [It can take up to 10 minutes for changes to your site to publish after you push the changes to GitHub](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/creating-a-github-pages-site-with-jekyll#creating-your-site).

[Jekyll]: https://jekyllrb.com
[Just the Docs]: https://just-the-docs.github.io/just-the-docs/
[GitHub Pages]: https://docs.github.com/en/pages
[GitHub Pages / Actions workflow]: https://github.blog/changelog/2022-07-27-github-pages-custom-github-actions-workflows-beta/
[Bundler]: https://bundler.io
[use this template]: https://github.com/just-the-docs/just-the-docs-template/generate
[`jekyll-default-layout`]: https://github.com/benbalter/jekyll-default-layout
[`jekyll-seo-tag`]: https://jekyll.github.io/jekyll-seo-tag
[MIT License]: https://en.wikipedia.org/wiki/MIT_License
[starter workflows]: https://github.com/actions/starter-workflows/blob/main/pages/jekyll.yml
[actions/starter-workflows]: https://github.com/actions/starter-workflows/blob/main/LICENSE
