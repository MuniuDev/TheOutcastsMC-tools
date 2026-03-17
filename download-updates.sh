#!/bin/bash
set -euo pipefail
# Paper
pushd updates


wget https://fill-data.papermc.io/v1/objects/da497e12b43e5b61c5df150e4bfd0de0f53043e57d2ac98dd59289ee9da4ad68/paper-1.21.11-127.jar

pushd plugins

# Core protect
wget https://www.patreon.com/file?h=145853143&m=580728422

# Essentials
wget https://ci.ender.zone/job/EssentialsX/lastSuccessfulBuild/artifact/jars/EssentialsX-2.22.0-dev+74-d7452bf.jar
wget https://ci.ender.zone/job/EssentialsX/lastSuccessfulBuild/artifact/jars/EssentialsXChat-2.22.0-dev+74-d7452bf.jar
wget https://ci.ender.zone/job/EssentialsX/lastSuccessfulBuild/artifact/jars/EssentialsXSpawn-2.22.0-dev+74-d7452bf.jar

# Bukkit
wget https://dev.bukkit.org/projects/dropheads/files/latest
wget https://dev.bukkit.org/projects/worldguard/files/latest
wget https://dev.bukkit.org/projects/openinv/files/latest
wget https://dev.bukkit.org/projects/multiverse-core/files/latest

# Modirinth
wget https://cdn.modrinth.com/data/O4o4mKaq/versions/dGfCZHqk/GriefPrevention.jar
wget https://cdn.modrinth.com/data/ijC5dDkD/versions/QdShnamC/QuickShop-Hikari-6.2.0.11.jar

# Spigot
wget https://www.spigotmc.org/resources/antibookban.89720/download?version=386572
wget https://www.spigotmc.org/resources/armor-stand-tools.2237/download?version=542201
wget https://www.spigotmc.org/resources/chunky.81534/download?version=594423
wget https://www.spigotmc.org/resources/doubleshulkershells.82365/download?version=348817
wget https://www.spigotmc.org/resources/gringotts.42071/download?version=501915
wget https://www.spigotmc.org/resources/luckperms.28140/download?version=590885
wget https://www.spigotmc.org/resources/protocollib.1997/download?version=602511
wget https://www.spigotmc.org/resources/sleep-most-1-8-1-21-x-the-most-advanced-sleep-plugin-available-percentage-animations.60623/download?version=620462
wget https://www.spigotmc.org/resources/survivalinvisiframes.80692/download?version=403197
wget https://www.spigotmc.org/resources/vault.34315/download?version=344916
wget https://www.spigotmc.org/resources/wandering-trades-easily-customize-wandering-traders-1-16-5-1-21-8.79068/
wget https://www.spigotmc.org/resources/abandoned-animated-tab-tablist.46229/download?version=554144
wget https://www.spigotmc.org/resources/fastasyncworldedit.13932/download?version=618458
wget https://www.spigotmc.org/resources/%E2%9C%A8-antipopup-no-chat-reports-and-popup-%E2%9C%A8.103782/download?version=622247
wget https://www.spigotmc.org/resources/dynmap%C2%AE.274/download?version=622292
wget https://www.spigotmc.org/resources/dynmap-griefprevention.98376/download?version=487925

popd
popd
