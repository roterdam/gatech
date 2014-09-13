# The Correlator is responsible for mapping an object in one dictionary
# to an object in another dictionary based on attribute similarity

class Correlator:

  def __init__(self, base_objects, target_objects):
    self.base_map           = {} # Map source objects to target objects
    self.target_map         = {} # Map target objects to base objects
    self.base_label_map     = {} # Map base objects to label
    self.target_label_map   = {} # Map target objects to label

    self.__correlate_objects(base_objects, target_objects)

  def get_base_correlation(self, name):
    if name not in self.base_map.keys():
      return None
    return self.base_map[name]

  def get_target_correlation(self, name):
    if name not in self.target_map.keys():
      return None
    return self.target_map[name]

  def get_base_label(self, name):
    if name not in self.base_label_map.keys():
      return None
    return self.base_label_map[name]

  def get_target_label(self, name):
    if name not in self.target_label_map.keys():
      return None
    return self.target_label_map[name]

  def translate_base_labels(self, labels):
    translated = []
    for value in labels:
      if self.get_base_label(value):
        translated.append(self.get_base_label(value))

    return ",".join(translated)

  def translate_target_labels(self, labels):
    translated = []
    for value in labels:
      if self.get_target_label(value):
        translated.append(self.get_target_label(value))

    return ",".join(translated)

  # Given two dictionaries of objects, return a list of object name pairs with unique label
  def __correlate_objects(self, base_objects, target_objects):
    # copy my target objects
    remaining_targets = target_objects

    # If we are dealing with a single object, correlate them and move on
    if (len(base_objects) == 1) & (len(target_objects) == 1):
      # Label with shape
      self.__store_correlation(base_objects[0].getName(), target_objects[0].getName(), self.__get_attribute_value(base_objects[0], 'shape'))

    # Cycle through the base objects and find the most similar correlating specifically
    # on shape, size, and position
    for base_object in base_objects:
      correlation_info = self.__correlate(base_object, remaining_targets, ['shape', 'size', 'above', 'below', 'left-of', 'right-of', 'inside'])
      if correlation_info:
        self.__store_correlation(correlation_info[0], correlation_info[1], correlation_info[2])
        # Rip this out of remaining_targets
        remaining_targets = [target for target in remaining_targets if target.getName() != self.get_base_correlation(base_object.getName())]


  def __store_correlation(self, base_name, target_name, label):
    self.base_map[base_name]            = target_name
    self.target_map[target_name]        = base_name
    self.base_label_map[base_name]      = label
    self.target_label_map[target_name]  = label


  # Find my buddy based on the passed in attributes. Return none if we can't find one
  def __correlate(self, base_object, target_objects, attributes = [], label = ''):
    if not attributes:
      return None

    # Cycle through the attributes filtering until we find a single match
    possibles = [target for target in target_objects if self.__same_attribute(attributes[0], base_object, target)]
    #print "Possibles for base object: " + base_object.getName() + " attribute: " + str(attributes[0]) + " - " + str([obj.getName() for obj in possibles])

    # If we didn't find anything throw out this attribute and continue down the line
    if not possibles:
      del(attributes[0])
      return self.__correlate(base_object, target_objects, attributes)

    # Store my label
    if label == '':
      custom_label = 'shape'
    else:
      custom_label = label + self.__get_attribute_value(possibles[0], attributes[0])

    # If we have a single result, we win!
    if len(possibles) == 1:
      #print "Found! Correlating: " + base_object.getName() + " with: " + possibles[0].getName()
      return [base_object.getName(), possibles[0].getName(), custom_label]

    # If we have more than one possible, continue down the list
    del(attributes[0])
    return self.__correlate(base_object, possibles, attributes, custom_label)

  # Does each object have the same attribute value for the provided attribute?
  def __same_attribute(self, attribute_name, base, target):
    # Det all attributes for base and target
    base_attributes   = base.getAttributes()
    target_attributes = target.getAttributes()

    # Does each attribute set have the attribute we are looking for?
    base_attribute    = [attribute for attribute in base_attributes if attribute.getName() == attribute_name]
    target_attribute  = [attribute for attribute in target_attributes if attribute.getName() == attribute_name]

    if not base_attribute:
      return False

    if not target_attribute:
      return False

    if base_attribute[0].getValue() != target_attribute[0].getValue():
      return False

    return True

  # Do I have an object with a matching label?
  def __matching_label(self, label, target_objects):
    matches = [target_object for target_object in target_objects if target_object.getName() == label]

    if matches:
      return True
    else:
      return False

  # Get the value of an attribute given a shape and attribute name
  def __get_attribute_value(self, object, attribute_name):
    attributes  = object.getAttributes()
    filtered    = [attribute for attribute in attributes if attribute.getName() == attribute_name]

    if not filtered:
      return None

    return filtered[0].getValue()

