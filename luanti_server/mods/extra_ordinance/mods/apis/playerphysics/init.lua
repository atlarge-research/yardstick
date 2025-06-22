playerphysics = {}

local function calculate_attribute_product(player, attribute)
	local a = minetest.deserialize(player:get_meta():get_string("playerphysics:physics"), true)
	local product = 1
	if a == nil or a[attribute] == nil then
		return product
	end
	local factors = a[attribute]
	if type(factors) == "table" then
		for _, factor in pairs(factors) do
			product = product * factor
		end
	end
	return product
end

function playerphysics.add_physics_factor(player, attribute, id, value)
	local meta = player:get_meta()
	local a = minetest.deserialize(meta:get_string("playerphysics:physics"), true)
	if a == nil then
		a = { [attribute] = { [id] = value } }
	elseif a[attribute] == nil then
		a[attribute] = { [id] = value }
	else
		a[attribute][id] = value
	end
	meta:set_string("playerphysics:physics", minetest.serialize(a))
	local raw_value = calculate_attribute_product(player, attribute)
	player:set_physics_override({[attribute] = raw_value})
end

function playerphysics.remove_all_physics_factors(player)
	local meta = player:get_meta()
	local a = minetest.deserialize(meta:get_string("playerphysics:physics"))
	local factors = {}
	for attribute, list in pairs(a) do
		factors[attribute] = 1
		a[attribute] = nil
	end
	meta:set_string("playerphysics:physics", minetest.serialize(a))
	player:set_physics_override(factors)
end

function playerphysics.remove_physics_factor(player, attribute, id)
	local meta = player:get_meta()
	local a = minetest.deserialize(meta:get_string("playerphysics:physics"), true)
	if a == nil or a[attribute] == nil then
		-- Nothing to remove
		return
	else
		a[attribute][id] = nil
	end
	meta:set_string("playerphysics:physics", minetest.serialize(a))
	local raw_value = calculate_attribute_product(player, attribute)
	player:set_physics_override({[attribute] = raw_value})
end

function playerphysics.get_physics_factor(player, attribute, id)
	local meta = player:get_meta()
	local a = minetest.deserialize(meta:get_string("playerphysics:physics"), true)
	if a == nil then
		return nil
	elseif a[attribute] == nil then
		return nil
	else
		return a[attribute][id]
	end
end
