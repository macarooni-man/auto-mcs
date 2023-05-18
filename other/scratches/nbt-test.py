from datetime import datetime as dt
from nbt import nbt
from munch import Munch
import re, json


class ItemObject(Munch):
    pass

class InventoryObject():

    def __init__(self, item_list, selected_item):

        self._item_list = []

        self.selected_item = ItemObject({})
        self.offhand = ItemObject({})
        self.hotbar = ItemObject({x: {} for x in range(0, 9)})
        self.inventory = ItemObject({x: {} for x in range(0, 27)})
        self.armor = ItemObject({'head': {}, 'chest': {}, 'legs': {}, 'feet': {}})

        self._process_items(item_list, selected_item)

    def __iter__(self):
        for item in self._item_list:
            yield item

    def _process_items(self, i, s):

        # Old items, parsing from playerdata
        if i.__class__.__name__ == "TAG_List":

            # Converts block/item/enchantment IDs to names
            def proc_nbt(item):

                # Add all root tags to formatted
                formatted = {}
                for x in item:

                    # Add all tag attributes to root.tag
                    if item[x].name == 'tag':
                        formatted[item[x].name] = {}
                        for tag in item[x]:
                            value = item[x][tag].value
                            formatted[item[x].name.lower()][item[x][tag].name.lower() if item[x][tag].name != "ench" else "enchantments"] = value if value else {}

                            # Format all enchantments
                            if item[x][tag].name.lower() in ["ench", "storedenchantments"]:
                                for e in item[x][tag]:
                                    formatted[item[x].name.lower()]['enchantments'][id_dict['enchant'].get(e['id'].value, e['id'].value)] = {'id': e['id'].value, 'lvl': e['lvl'].value}

                            # Format all display items
                            elif item[x][tag].name.lower() == "display":
                                for d in item[x][tag]:
                                    if d == "Lore":
                                        value = '\n'.join([line.value for line in item[x][tag][d]])
                                    else:
                                        value = item[x][tag][d].value

                                        if d == "Name":
                                            # Add to item list for __iter__ function
                                            if value not in self._item_list:
                                                self._item_list.append(value)

                                    formatted[item[x].name.lower()][item[x][tag].name][item[x][tag][d].name.lower()] = value

                            # Attributes
                            elif item[x][tag].name.lower() == "attributemodifiers":
                                formatted[item[x].name.lower()]['attributemodifiers'] = []
                                for y in item[x][tag].tags:
                                    attr_dict = {y[a].name.lower(): y[a].value for a in y}
                                    formatted[item[x].name.lower()]['attributemodifiers'].append(attr_dict)

                            # Format all book pages
                            elif item[x][tag].name.lower() == "pages":
                                formatted[item[x].name.lower()]['pages'] = [y for y in item[x][tag].tags]


                    elif item[x].name == 'id':
                        try:
                            value = item[x].value[item[x].value.find(':')+1:]
                        except AttributeError:
                            value = id_dict['items'][item[x].value].split(":")[1]

                        # Add to item list for __iter__ function
                        if value not in self._item_list:
                            self._item_list.append(value)

                        formatted[item[x].name.lower()] = value


                    elif item[x].name != 'Slot':
                        formatted[item[x].name.lower()] = item[x].value


                return ItemObject(formatted)

            # Iterates over every item in inventory
            def sort_item(item):

                # Hotbar
                if fmt(item['Slot']) in range(0, 9):
                    self.hotbar[fmt(item['Slot'])] = proc_nbt(item)

                # Offhand
                elif fmt(item['Slot']) == 99:
                    self.offhand = proc_nbt(item)

                # Feet
                elif fmt(item['Slot']) == 100:
                    self.armor.feet = proc_nbt(item)

                # Legs
                elif fmt(item['Slot']) == 101:
                    self.armor.legs = proc_nbt(item)

                # Chest
                elif fmt(item['Slot']) == 102:
                    self.armor.chest = proc_nbt(item)

                # Head
                elif fmt(item['Slot']) == 103:
                    self.armor.head = proc_nbt(item)

                # Inventory
                else:
                    self.inventory[fmt(item['Slot'])-9] = proc_nbt(item)

            for item in i.tags:
                sort_item(item)

            if selected_item:
                self.selected_item = proc_nbt(selected_item)


id_dict = {
    'effect': {
        1:  'speed',
        2:  'slowness',
        3:  'haste',
        4:  'mining_fatigue',
        5:  'strength',
        6:  'instant_health',
        7:  'instant_damage',
        8:  'jump_boost',
        9:  'nausea',
        10: 'regeneration',
        11: 'resistance',
        12: 'fire_resistance',
        13: 'water_breathing',
        14: 'invisibility',
        15: 'blindness',
        16: 'night_vision',
        17: 'hunger',
        18: 'weakness',
        19: 'poison',
        20: 'wither',
        21: 'health_boost',
        22: 'absorption',
        23: 'saturation',
        24: 'glowing',
        25: 'levitation',
        26: 'luck',
        27: 'unluck',
        28: 'slow_falling',
        29: 'conduit_power',
        30: 'dolphins_grace',
        31: 'bad_omen',
        32: 'hero_of_the_village',
        33: 'darkness',
        34: 'big',
        35: 'small'
    },
    'enchant': {
        0:  'protection',
        1:  'fire_protection',
        2:  'feather_falling',
        3:  'blast_protection',
        4:  'projectile_protection',
        5:  'respiration',
        6:  'aqua_affinity',
        7:  'thorns',
        8:  'depth_strider',
        10: 'binding_curse',
        16: 'sharpness',
        17: 'smite',
        18: 'bane_of_arthropods',
        19: 'knockback',
        20: 'fire_aspect',
        21: 'looting',
        22: 'sweeping',
        32: 'efficiency',
        33: 'silk_touch',
        34: 'unbreaking',
        35: 'fortune',
        48: 'power',
        49: 'punch',
        50: 'flame',
        51: 'infinity',
        61: 'luck_of_the_sea',
        62: 'lure',
        65: 'loyalty',
        66: 'impaling',
        67: 'riptide',
        68: 'channeling',
        70: 'mending',
        71: 'vanishing_curse'
    },
    'items': {
        0:    'minecraft:air',
        1:    'minecraft:stone',
        2:    'minecraft:grass',
        3:    'minecraft:dirt',
        4:    'minecraft:cobblestone',
        5:    'minecraft:planks',
        6:    'minecraft:sapling',
        7:    'minecraft:bedrock',
        8:    'minecraft:flowing_water',
        9:    'minecraft:water',
        10:   'minecraft:flowing_lava',
        11:   'minecraft:lava',
        12:   'minecraft:sand',
        13:   'minecraft:gravel',
        14:   'minecraft:gold_ore',
        15:   'minecraft:iron_ore',
        16:   'minecraft:coal_ore',
        17:   'minecraft:log',
        18:   'minecraft:leaves',
        19:   'minecraft:sponge',
        20:   'minecraft:glass',
        21:   'minecraft:lapis_ore',
        22:   'minecraft:lapis_block',
        23:   'minecraft:dispenser',
        24:   'minecraft:sandstone',
        25:   'minecraft:noteblock',
        26:   'minecraft:bed',
        27:   'minecraft:golden_rail',
        28:   'minecraft:detector_rail',
        29:   'minecraft:sticky_piston',
        30:   'minecraft:web',
        31:   'minecraft:tallgrass',
        32:   'minecraft:deadbush',
        33:   'minecraft:piston',
        34:   'minecraft:piston_head',
        35:   'minecraft:wool',
        37:   'minecraft:yellow_flower',
        38:   'minecraft:red_flower',
        39:   'minecraft:brown_mushroom',
        40:   'minecraft:red_mushroom',
        41:   'minecraft:gold_block',
        42:   'minecraft:iron_block',
        43:   'minecraft:double_stone_slab',
        44:   'minecraft:stone_slab',
        45:   'minecraft:brick_block',
        46:   'minecraft:tnt',
        47:   'minecraft:bookshelf',
        48:   'minecraft:mossy_cobblestone',
        49:   'minecraft:obsidian',
        50:   'minecraft:torch',
        51:   'minecraft:fire',
        52:   'minecraft:mob_spawner',
        53:   'minecraft:oak_stairs',
        54:   'minecraft:chest',
        55:   'minecraft:redstone_wire',
        56:   'minecraft:diamond_ore',
        57:   'minecraft:diamond_block',
        58:   'minecraft:crafting_table',
        59:   'minecraft:wheat',
        60:   'minecraft:farmland',
        61:   'minecraft:furnace',
        62:   'minecraft:lit_furnace',
        63:   'minecraft:standing_sign',
        64:   'minecraft:wooden_door',
        65:   'minecraft:ladder',
        66:   'minecraft:rail',
        67:   'minecraft:stone_stairs',
        68:   'minecraft:wall_sign',
        69:   'minecraft:lever',
        70:   'minecraft:stone_pressure_plate',
        71:   'minecraft:iron_door',
        72:   'minecraft:wooden_pressure_plate',
        73:   'minecraft:redstone_ore',
        74:   'minecraft:lit_redstone_ore',
        75:   'minecraft:unlit_redstone_torch',
        76:   'minecraft:redstone_torch',
        77:   'minecraft:stone_button',
        78:   'minecraft:snow_layer',
        79:   'minecraft:ice',
        80:   'minecraft:snow',
        81:   'minecraft:cactus',
        82:   'minecraft:clay',
        83:   'minecraft:reeds',
        84:   'minecraft:jukebox',
        85:   'minecraft:fence',
        86:   'minecraft:pumpkin',
        87:   'minecraft:netherrack',
        88:   'minecraft:soul_sand',
        89:   'minecraft:glowstone',
        90:   'minecraft:portal',
        91:   'minecraft:lit_pumpkin',
        92:   'minecraft:cake',
        93:   'minecraft:unpowered_repeater',
        94:   'minecraft:powered_repeater',
        95:   'minecraft:stained_glass',
        96:   'minecraft:trapdoor',
        97:   'minecraft:monster_egg',
        98:   'minecraft:stonebrick',
        99:   'minecraft:brown_mushroom_block',
        100:  'minecraft:red_mushroom_block',
        101:  'minecraft:iron_bars',
        102:  'minecraft:glass_pane',
        103:  'minecraft:melon_block',
        104:  'minecraft:pumpkin_stem',
        105:  'minecraft:melon_stem',
        106:  'minecraft:vine',
        107:  'minecraft:fence_gate',
        108:  'minecraft:brick_stairs',
        109:  'minecraft:stone_brick_stairs',
        110:  'minecraft:mycelium',
        111:  'minecraft:waterlily',
        112:  'minecraft:nether_brick',
        113:  'minecraft:nether_brick_fence',
        114:  'minecraft:nether_brick_stairs',
        115:  'minecraft:nether_wart',
        116:  'minecraft:enchanting_table',
        117:  'minecraft:brewing_stand',
        118:  'minecraft:cauldron',
        119:  'minecraft:end_portal',
        120:  'minecraft:end_portal_frame',
        121:  'minecraft:end_stone',
        122:  'minecraft:dragon_egg',
        123:  'minecraft:redstone_lamp',
        124:  'minecraft:lit_redstone_lamp',
        125:  'minecraft:double_wooden_slab',
        126:  'minecraft:wooden_slab',
        127:  'minecraft:cocoa',
        128:  'minecraft:sandstone_stairs',
        129:  'minecraft:emerald_ore',
        130:  'minecraft:ender_chest',
        131:  'minecraft:tripwire_hook',
        132:  'minecraft:tripwire_hook',
        133:  'minecraft:emerald_block',
        134:  'minecraft:spruce_stairs',
        135:  'minecraft:birch_stairs',
        136:  'minecraft:jungle_stairs',
        137:  'minecraft:command_block',
        138:  'minecraft:beacon',
        139:  'minecraft:cobblestone_wall',
        140:  'minecraft:flower_pot',
        141:  'minecraft:carrots',
        142:  'minecraft:potatoes',
        143:  'minecraft:wooden_button',
        144:  'minecraft:skull',
        145:  'minecraft:anvil',
        146:  'minecraft:trapped_chest',
        147:  'minecraft:light_weighted_pressure_plate',
        148:  'minecraft:heavy_weighted_pressure_plate',
        149:  'minecraft:unpowered_comparator',
        150:  'minecraft:powered_comparator',
        151:  'minecraft:daylight_detector',
        152:  'minecraft:redstone_block',
        153:  'minecraft:quartz_ore',
        154:  'minecraft:hopper',
        155:  'minecraft:quartz_block',
        156:  'minecraft:quartz_stairs',
        157:  'minecraft:activator_rail',
        158:  'minecraft:dropper',
        159:  'minecraft:stained_hardened_clay',
        160:  'minecraft:stained_glass_pane',
        161:  'minecraft:leaves2',
        162:  'minecraft:log2',
        163:  'minecraft:acacia_stairs',
        164:  'minecraft:dark_oak_stairs',
        165:  'minecraft:slime',
        166:  'minecraft:barrier',
        167:  'minecraft:iron_trapdoor',
        168:  'minecraft:prismarine',
        169:  'minecraft:sea_lantern',
        170:  'minecraft:hay_block',
        171:  'minecraft:carpet',
        172:  'minecraft:hardened_clay',
        173:  'minecraft:coal_block',
        174:  'minecraft:packed_ice',
        175:  'minecraft:double_plant',
        176:  'minecraft:standing_banner',
        177:  'minecraft:wall_banner',
        178:  'minecraft:daylight_detector_inverted',
        179:  'minecraft:red_sandstone',
        180:  'minecraft:red_sandstone_stairs',
        181:  'minecraft:double_stone_slab2',
        182:  'minecraft:stone_slab2',
        183:  'minecraft:spruce_fence_gate',
        184:  'minecraft:birch_fence_gate',
        185:  'minecraft:jungle_fence_gate',
        186:  'minecraft:dark_oak_fence_gate',
        187:  'minecraft:acacia_fence_gate',
        188:  'minecraft:spruce_fence',
        189:  'minecraft:birch_fence',
        190:  'minecraft:jungle_fence',
        191:  'minecraft:dark_oak_fence',
        192:  'minecraft:acacia_fence',
        193:  'minecraft:spruce_door',
        194:  'minecraft:birch_door',
        195:  'minecraft:jungle_door',
        196:  'minecraft:acacia_door',
        197:  'minecraft:dark_oak_door',
        198:  'minecraft:end_rod',
        199:  'minecraft:chorus_plant',
        200:  'minecraft:chorus_flower',
        201:  'minecraft:purpur_block',
        202:  'minecraft:purpur_pillar',
        203:  'minecraft:purpur_stairs',
        204:  'minecraft:purpur_double_slab',
        205:  'minecraft:purpur_slab',
        206:  'minecraft:end_bricks',
        207:  'minecraft:beetroots',
        208:  'minecraft:grass_path',
        209:  'minecraft:end_gateway',
        210:  'minecraft:repeating_command_block',
        211:  'minecraft:chain_command_block',
        212:  'minecraft:frosted_ice',
        213:  'minecraft:magma',
        214:  'minecraft:nether_wart_block',
        215:  'minecraft:red_nether_brick',
        216:  'minecraft:bone_block',
        217:  'minecraft:structure_void',
        218:  'minecraft:observer',
        219:  'minecraft:white_shulker_box',
        220:  'minecraft:orange_shulker_box',
        221:  'minecraft:magenta_shulker_box',
        222:  'minecraft:light_blue_shulker_box',
        223:  'minecraft:yellow_shulker_box',
        224:  'minecraft:lime_shulker_box',
        225:  'minecraft:pink_shulker_box',
        226:  'minecraft:gray_shulker_box',
        227:  'minecraft:silver_shulker_box',
        228:  'minecraft:cyan_shulker_box',
        229:  'minecraft:purple_shulker_box',
        230:  'minecraft:blue_shulker_box',
        231:  'minecraft:brown_shulker_box',
        232:  'minecraft:green_shulker_box',
        233:  'minecraft:red_shulker_box',
        234:  'minecraft:black_shulker_box',
        235:  'minecraft:white_glazed_terracotta',
        236:  'minecraft:orange_glazed_terracotta',
        237:  'minecraft:magenta_glazed_terracotta',
        238:  'minecraft:light_blue_glazed_terracotta',
        239:  'minecraft:yellow_glazed_terracotta',
        240:  'minecraft:lime_glazed_terracotta',
        241:  'minecraft:pink_glazed_terracotta',
        242:  'minecraft:gray_glazed_terracotta',
        243:  'minecraft:light_gray_glazed_terracotta',
        244:  'minecraft:cyan_glazed_terracotta',
        245:  'minecraft:purple_glazed_terracotta',
        246:  'minecraft:blue_glazed_terracotta',
        247:  'minecraft:brown_glazed_terracotta',
        248:  'minecraft:green_glazed_terracotta',
        249:  'minecraft:red_glazed_terracotta',
        250:  'minecraft:black_glazed_terracotta',
        251:  'minecraft:concrete',
        252:  'minecraft:concrete_powder',
        255:  'minecraft:structure_block',
        256:  'minecraft:iron_shovel',
        257:  'minecraft:iron_pickaxe',
        258:  'minecraft:iron_axe',
        259:  'minecraft:flint_and_steel',
        260:  'minecraft:apple',
        261:  'minecraft:bow',
        262:  'minecraft:arrow',
        263:  'minecraft:coal',
        264:  'minecraft:diamond',
        265:  'minecraft:iron_ingot',
        266:  'minecraft:gold_ingot',
        267:  'minecraft:iron_sword',
        268:  'minecraft:wooden_sword',
        269:  'minecraft:wooden_shovel',
        270:  'minecraft:wooden_pickaxe',
        271:  'minecraft:wooden_axe',
        272:  'minecraft:stone_sword',
        273:  'minecraft:stone_shovel',
        274:  'minecraft:stone_pickaxe',
        275:  'minecraft:stone_axe',
        276:  'minecraft:diamond_sword',
        277:  'minecraft:diamond_shovel',
        278:  'minecraft:diamond_pickaxe',
        279:  'minecraft:diamond_axe',
        280:  'minecraft:stick',
        281:  'minecraft:bowl',
        282:  'minecraft:mushroom_stew',
        283:  'minecraft:golden_sword',
        284:  'minecraft:golden_shovel',
        285:  'minecraft:golden_pickaxe',
        286:  'minecraft:golden_axe',
        287:  'minecraft:string',
        288:  'minecraft:feather',
        289:  'minecraft:gunpowder',
        290:  'minecraft:wooden_hoe',
        291:  'minecraft:stone_hoe',
        292:  'minecraft:iron_hoe',
        293:  'minecraft:diamond_hoe',
        294:  'minecraft:golden_hoe',
        295:  'minecraft:wheat_seeds',
        296:  'minecraft:wheat',
        297:  'minecraft:bread',
        298:  'minecraft:leather_helmet',
        299:  'minecraft:leather_chestplate',
        300:  'minecraft:leather_leggings',
        301:  'minecraft:leather_boots',
        302:  'minecraft:chainmail_helmet',
        303:  'minecraft:chainmail_chestplate',
        304:  'minecraft:chainmail_leggings',
        305:  'minecraft:chainmail_boots',
        306:  'minecraft:iron_helmet',
        307:  'minecraft:iron_chestplate',
        308:  'minecraft:iron_leggings',
        309:  'minecraft:iron_boots',
        310:  'minecraft:diamond_helmet',
        311:  'minecraft:diamond_chestplate',
        312:  'minecraft:diamond_leggings',
        313:  'minecraft:diamond_boots',
        314:  'minecraft:golden_helmet',
        315:  'minecraft:golden_chestplate',
        316:  'minecraft:golden_leggings',
        317:  'minecraft:golden_boots',
        318:  'minecraft:flint',
        319:  'minecraft:porkchop',
        320:  'minecraft:cooked_porkchop',
        321:  'minecraft:painting',
        322:  'minecraft:golden_apple',
        323:  'minecraft:sign',
        324:  'minecraft:wooden_door',
        325:  'minecraft:bucket',
        326:  'minecraft:water_bucket',
        327:  'minecraft:lava_bucket',
        328:  'minecraft:minecart',
        329:  'minecraft:saddle',
        330:  'minecraft:iron_door',
        331:  'minecraft:redstone',
        332:  'minecraft:snowball',
        333:  'minecraft:boat',
        334:  'minecraft:leather',
        335:  'minecraft:milk_bucket',
        336:  'minecraft:brick',
        337:  'minecraft:clay_ball',
        338:  'minecraft:reeds',
        339:  'minecraft:paper',
        340:  'minecraft:book',
        341:  'minecraft:slime_ball',
        342:  'minecraft:chest_minecart',
        343:  'minecraft:furnace_minecart',
        344:  'minecraft:egg',
        345:  'minecraft:compass',
        346:  'minecraft:fishing_rod',
        347:  'minecraft:clock',
        348:  'minecraft:glowstone_dust',
        349:  'minecraft:fish',
        350:  'minecraft:cooked_fish',
        351:  'minecraft:dye',
        352:  'minecraft:bone',
        353:  'minecraft:sugar',
        354:  'minecraft:cake',
        355:  'minecraft:bed',
        356:  'minecraft:repeater',
        357:  'minecraft:cookie',
        358:  'minecraft:filled_map',
        359:  'minecraft:shears',
        360:  'minecraft:melon',
        361:  'minecraft:pumpkin_seeds',
        362:  'minecraft:melon_seeds',
        363:  'minecraft:beef',
        364:  'minecraft:cooked_beef',
        365:  'minecraft:chicken',
        366:  'minecraft:cooked_chicken',
        367:  'minecraft:rotten_flesh',
        368:  'minecraft:ender_pearl',
        369:  'minecraft:blaze_rod',
        370:  'minecraft:ghast_tear',
        371:  'minecraft:gold_nugget',
        372:  'minecraft:nether_wart',
        373:  'minecraft:potion',
        374:  'minecraft:glass_bottle',
        375:  'minecraft:spider_eye',
        376:  'minecraft:fermented_spider_eye',
        377:  'minecraft:blaze_powder',
        378:  'minecraft:magma_cream',
        379:  'minecraft:brewing_stand',
        380:  'minecraft:cauldron',
        381:  'minecraft:ender_eye',
        382:  'minecraft:speckled_melon',
        383:  'minecraft:spawn_egg',
        384:  'minecraft:experience_bottle',
        385:  'minecraft:fire_charge',
        386:  'minecraft:writable_book',
        387:  'minecraft:written_book',
        388:  'minecraft:emerald',
        389:  'minecraft:item_frame',
        390:  'minecraft:flower_pot',
        391:  'minecraft:carrot',
        392:  'minecraft:potato',
        393:  'minecraft:baked_potato',
        394:  'minecraft:poisonous_potato',
        395:  'minecraft:map',
        396:  'minecraft:golden_carrot',
        397:  'minecraft:skull',
        398:  'minecraft:carrot_on_a_stick',
        399:  'minecraft:nether_star',
        400:  'minecraft:pumpkin_pie',
        401:  'minecraft:fireworks',
        402:  'minecraft:firework_charge',
        403:  'minecraft:enchanted_book',
        404:  'minecraft:comparator',
        405:  'minecraft:netherbrick',
        406:  'minecraft:quartz',
        407:  'minecraft:tnt_minecart',
        408:  'minecraft:hopper_minecart',
        409:  'minecraft:prismarine_shard',
        410:  'minecraft:prismarine_crystals',
        411:  'minecraft:rabbit',
        412:  'minecraft:cooked_rabbit',
        413:  'minecraft:rabbit_stew',
        414:  'minecraft:rabbit_foot',
        415:  'minecraft:rabbit_hide',
        416:  'minecraft:armor_stand',
        417:  'minecraft:iron_horse_armor',
        418:  'minecraft:golden_horse_armor',
        419:  'minecraft:diamond_horse_armor',
        420:  'minecraft:lead',
        421:  'minecraft:name_tag',
        422:  'minecraft:command_block_minecart',
        423:  'minecraft:mutton',
        424:  'minecraft:cooked_mutton',
        425:  'minecraft:banner',
        426:  'minecraft:end_crystal',
        427:  'minecraft:spruce_door',
        428:  'minecraft:birch_door',
        429:  'minecraft:jungle_door',
        430:  'minecraft:acacia_door',
        431:  'minecraft:dark_oak_door',
        432:  'minecraft:chorus_fruit',
        433:  'minecraft:popped_chorus_fruit',
        434:  'minecraft:beetroot',
        435:  'minecraft:beetroot_seeds',
        436:  'minecraft:beetroot_soup',
        437:  'minecraft:dragon_breath',
        438:  'minecraft:splash_potion',
        439:  'minecraft:spectral_arrow',
        440:  'minecraft:tipped_arrow',
        441:  'minecraft:lingering_potion',
        442:  'minecraft:shield',
        443:  'minecraft:elytra',
        444:  'minecraft:spruce_boat',
        445:  'minecraft:birch_boat',
        446:  'minecraft:jungle_boat',
        447:  'minecraft:acacia_boat',
        448:  'minecraft:dark_oak_boat',
        449:  'minecraft:totem_of_undying',
        450:  'minecraft:shulker_shell',
        452:  'minecraft:iron_nugget',
        453:  'minecraft:knowledge_book',
        2256: 'minecraft:record_13',
        2257: 'minecraft:record_cat',
        2258: 'minecraft:record_blocks',
        2259: 'minecraft:record_chirp',
        2260: 'minecraft:record_far',
        2261: 'minecraft:record_mall',
        2262: 'minecraft:record_mellohi',
        2263: 'minecraft:record_stal',
        2264: 'minecraft:record_strad',
        2265: 'minecraft:record_ward',
        2266: 'minecraft:record_11',
        2267: 'minecraft:record_wait'
    }
}

def fmt(obj):
    return round(float(obj.value), 4)






# Pre 1.13:

# file = nbt.NBTFile(r"C:\Users\macarooni machine\AppData\Roaming\.auto-mcs\Servers\b1.4 MACX\world\players\KChicken.dat", "rb")
# print(file)


# print('position',           {'x': fmt(file['Pos'][0]), 'y': fmt(file['Pos'][1]), 'z': fmt(file['Pos'][2])})
# print('rotation',           {'x': fmt(file['Rotation'][0]), 'y': fmt(file['Rotation'][1])})
# print('motion',             {'x': fmt(file['Motion'][0]), 'y': fmt(file['Motion'][1]), 'z': fmt(file['Motion'][2])})
# print('spawn_position',     {'x': fmt(file['SpawnX']), 'y': fmt(file['SpawnY']), 'z': fmt(file['SpawnZ'])})
# print('health',             int(file['Health'].value))
# print('hunger',             int(file['foodLevel'].value))
# print('gamemode',           ['survival', 'creative', 'adventure', 'spectator'][int(file['playerGameType'].value)])
# print('xp',                 round(float(file['XpLevel'].value) + float(file['XpP'].value), 3))
# print('hurt_time',          int(file['HurtTime'].value))
# print('death_time',         int(file['DeathTime'].value))
# print('sleeping',           (int(file['Sleeping'].value) == 1))
# print('dimension',          {0: 'overworld', -1: 'nether', 1: 'end'}.get(int(file['Dimension'].value), int(file['Dimension'].value)))
# print('active_effects',     {id_dict['effect'].get(item[3].value, item[3].value): {'id': item[3].value, 'amplitude': int(item[4].value), 'duration': int(item[2].value), 'show_particles': (item[1].value == 1)} for item in file['ActiveEffects'].tags})

# try:
#     selected_item = file['SelectedItem']
# except KeyError:
#     selected_item = None
#
# # test = dt.now()
# # print('inventory:', vars(InventoryObject(file['Inventory'], selected_item)))
# # print(dt.now() - test)
#
# inventory = InventoryObject(file['Inventory'], selected_item)
#
# print(inventory.armor.head)
# print(inventory.selected_item)
# print(inventory.hotbar[3])
#
# print(inventory._item_list)
# print(("wooden_hoe" in inventory))








# Post 1.13
