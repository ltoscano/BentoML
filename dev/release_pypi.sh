#!/usr/bin/env bash
set -e

if [ "$#" -eq 1 ]; then
  VERSION_STR=$1
else
  echo "Must provide release version string, e.g. ./script/release.sh 1.0.5"
  exit 1
fi

SEMVER_REGEX="^[vV]?(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(\\-[0-9A-Za-z-]+(\\.[0-9A-Za-z-]+)*)?(\\+[0-9A-Za-z-]+(\\.[0-9A-Za-z-]+)*)?$"

if [[ "$VERSION_STR" =~ $SEMVER_REGEX ]]; then
  echo "Releasing bentoml version v$VERSION_STR:"
else
  echo "Version $VERSION_STR must follow semantic versioning schema"
  exit 1
fi

GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"

# Currently only BentoML maintainer has permission to create new pypi
# releases
if [ ! -f "$HOME"/.pypirc ]; then
  # about .pypirc file:
  # https://docs.python.org/3/distutils/packageindex.html#the-pypirc-file
  echo "Error: File \$HOME/.pypirc not found."
  exit 1
fi


if [ -d "$GIT_ROOT"/dist ]; then
  echo "Removing existing 'dist' and 'build' directory to get a clean build"
  rm -rf "$GIT_ROOT"/dist
  rm -rf "$GIT_ROOT"/build
fi

tag_name="v$VERSION_STR"

echo "Installing dev dependencies..."
pip install .[dev]

echo "Installing YataiServer node server dependencies.."
cd "$GIT_ROOT"/bentoml/yatai/web
yarn

echo "Installing YataiServer Web UI dependencies.."
cd "$GIT_ROOT"/bentoml/yatai/web/client
yarn

echo "Build YataiServer node server and web UI..."
cd "$GIT_ROOT"/bentoml/yatai/web
yarn build

if git rev-parse "$tag_name" >/dev/null 2>&1; then
  echo "git tag '$tag_name' exist, using existing tag."
  echo "To redo releasing and overwrite existing tag, delete tag with the following and re-run release.sh:"
  echo "git tag -d $tag_name && git push --delete origin $tag_name"
  git checkout "$tag_name"
else
  echo "Creating git tag '$tag_name'"
  git tag -a "$tag_name" -m "Tag generated by BentoML/script/release.sh, version: $VERSION_STR"
  git push origin "$tag_name"
fi

echo "Generating PyPI source distribution..."
cd "$GIT_ROOT"
python3 setup.py sdist bdist_wheel

# Use testpypi by default, run script with: "REPO=pypi release.sh" for
# releasing to Pypi.org
REPO=${REPO:=testpypi}

echo "Uploading PyPI package to $REPO..."
twine upload --repository $REPO dist/* --verbose

echo "Done releasing BentoML version:$VERSION_STR"
