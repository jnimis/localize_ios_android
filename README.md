# localize_ios_android
Python 3 scripts for generating, formatting, merging iOS localization files, and creating Android resources

**NOTICE**: **use at your own risk** I built this for a specific project, developing iOS and Android concurrently, and haven't tested it outside of my own environment

The main script is based on this gist: https://gist.github.com/yoichitgy/29bdd71c3556c2055cc0

**note**: I disabled the method that creates new keys for each NSLocalizableString key in your code, because I'm using a different implementation of localizable, but this would be easy enough to re-enable

1. Place these scripts in a subdirectory of your iOS project, e.g. .../{projectRoot}/bin
2. Add a build phase to your XCode project to run this command:
    python3 bin/mergegenstrings.py {folderWithYourCode}
3. Build your project, and you should end up with:
  * .strings files for each UI element, merged with existing localization values, alphabetized by key
  * an alphabetized Localizable.strings file (this file still has to be managed manually, see note above)
  * an xml folder with Android resources, in res/values(-lang)/strings.xml
    * each strings.xml file is divided with comments to delineate which iOS resources each block came from
