from Correlator import *

# The GenerateTest class is used to generate a solution to a Ravens progressive
# Matrix using the Generate and Test strategy.
class GenerateTest:
  def find_solution(self, problem):
    print "Run Generate and Test solver against: " + problem.getName()

    # The first thing we need to do is ask the Generator to generate a list
    # of possible solutions to this problem
    candidates = Generator(problem).generate_candidates()

    # Given a list of candidates, test against our available answers and provide
    # a winner
    return Tester(problem).choose_answer(candidates)

# The Generate class is responsible for generating a list of possible solution candidates
class Generator:
  def __init__(self, problem):
    self.problem  = problem

  def generate_candidates(self):
    candidates    = []

    # Generate a set of transforms between A and B using all operators
    candidates.append(self.generate_transforms("A", "B"))

    # Try ignoring position
    #candidates.append(self.generate_transforms("A", "B", ["above","below","left-of","right-of"]))

    # Try fuzzy angles
    candidates.append(self.generate_transforms("A", "B", [], True))

    # Return a set of transforms, or diffs, we think would be acceptable solutions
    return candidates

  # Generate a Dictionary of attribute changes per object
  def generate_transforms(self, start_name, end_name, ignore = [], fuzzy_angles = False):
    transforms      = []

    # Retrieve the start and end figures
    try:
      start_figure  = self.__retrieve_figure(start_name)
      end_figure    = self.__retrieve_figure(end_name)
    except FigureNotFoundError as e:
      print "Unable to retrieve figure(s): " + str(e)
      return []

    # Retrieve the objects for both the start and the end figures
    start_objects = start_figure.getObjects();
    end_objects   = end_figure.getObjects();

    # Correlate the objects between the start and end figures
    correlated_objects = Correlator(start_objects, end_objects)

    # Cycle through each object in the start figure and look for differences
    # in the same object in the end figure. Additions and deletions will show
    # as None in the before or end state.
    for start_obj in start_objects:
      # Does this object correlate to one in the end figure?
      if not correlated_objects.get_base_correlation(start_obj.getName()):
        continue

      end_obj = [entity for entity in end_objects if entity.getName() == correlated_objects.get_base_correlation(start_obj.getName())]
      if not end_obj:
        print 'Something bad hapened when retrieving a correlated object'
        continue
      else:
        end_obj = end_obj[0]

      # Now we have both objects, define the differences
      start_attributes  = start_obj.getAttributes()
      end_attributes    = end_obj.getAttributes()

      attribute_transform = self.compare_attributes(start_attributes, end_attributes, correlated_objects, ignore, fuzzy_angles)

      if attribute_transform:
        transforms.append(attribute_transform)

    return transforms

  # Compare two sets of attributes and return the transforms
  # We can alternatively pass in a set of attributes to ignore
  def compare_attributes(self, start_attributes, end_attributes, correlations, ignore = [], fuzzy_angles = False):
    attribute_transforms = { }
    for start_attribute in start_attributes:
      if start_attribute.getName() in ignore:
        continue
      end_attribute = [ attribute for attribute in end_attributes if attribute.getName() == start_attribute.getName() ]
      if not end_attribute:
        if start_attribute.getName() in ['above', 'below', 'left-of', 'right-of', 'inside']:
          attribute_transforms[start_attribute.getName()] = [ correlations.translate_base_labels(start_attribute.getValue().split(',')), None ]
        else:
          attribute_transforms[start_attribute.getName()] = [ start_attribute.getValue(), None ]
        continue
      else:
        end_attribute = end_attribute[0]

      if start_attribute.getValue() != end_attribute.getValue():
        if start_attribute.getName() == "angle":
          # should I be fuzzy with my angle calculations?
          if fuzzy_angles:
            attribute_transforms[ start_attribute.getName() ] = self.__compute_angle_change(start_attribute.getValue(), end_attribute.getValue())
          else:
            attribute_transforms[ start_attribute.getName() ] = abs(int(start_attribute.getValue()) - int(end_attribute.getValue()))
        # If this is location data, we need to use our generated labels
        elif start_attribute.getName() in ['above', 'below', 'left-of', 'right-of', 'inside']:
          # These values are lists of ID's.  Transfer them to custom labels.
          attribute_transforms[ start_attribute.getName() ] = [ correlations.translate_base_labels(start_attribute.getValue().split(',')), correlations.translate_target_labels(start_attribute.getValue().split(',')) ]
        else:
          attribute_transforms[ start_attribute.getName() ] = [ start_attribute.getValue(), end_attribute.getValue() ]

    # Get attributes in the end state not in the beginning state
    for end_attribute in end_attributes:
      if end_attribute.getName() in ignore:
        continue
      start_attribute = [ attribute for attribute in start_attributes if attribute.getName() == end_attribute.getName() ]
      if not start_attribute:
        if end_attribute.getName() in ['above', 'below', 'left-of', 'right-of', 'inside']:
          attribute_transforms[end_attribute.getName()] = [ None, correlations.translate_target_labels(end_attribute.getValue().split(',')) ]
        else:
          attribute_transforms[end_attribute.getName()] = [ end_attribute.getValue(), None ]
        continue

    return attribute_transforms

  def __retrieve_figure(self, figure_name):
    figure = self.problem.getFigures().get(figure_name)
    if not figure:
      raise FigureNotFoundError("Figure not found: " + figure_name)

    return figure

  # Try to be a bit smarter about detecting angle differences
  def __compute_angle_change(self, start, end):
    # What is the net angle change?
    total_difference = abs(int(start) - int(end))

    if total_difference > 180:
      # This can also be looked at as a negative angle change
      return 360 - total_difference
    else:
      return total_difference

# The Tester class is responsible for making a best guess on a solution
# given a set of generated solutions and a set of possible answers.
class Tester:
  def __init__(self, problem):
    self.problem  = problem

  # Process our candidte transforms and choose a solution
  def choose_answer(self, candidates):
    for candidate in candidates:
      # Was there a common transform to all objects?  Can I apply that transform to all objects in target?
      if self.__all_objects_transformed("A", candidate):
        common_transform = self.__common_transform(candidate)
        if common_transform:
          # apply the common transform to every object in C and see if we can match the solution
          solutions = [str(figure) for figure in range(1,7) if cmp(self.__applied_common_transform("C",common_transform), Generator(self.problem).generate_transforms("C", str(figure))) == 0]

          if solutions:
            return solutions[0]

          # Is the common transform an angle?  If so, apply some special cases
          if "angle" in common_transform.keys():
            # If the angle differential is 180, and we are moving from a symetrical image to an asymetrical image, check for reflection
            # by adding a vertical flip
            if common_transform["angle"] == 180:
              vertical_transform = common_transform
              vertical_transform['vertical-flip'] = ['no', 'yes']
              solutions = [str(figure) for figure in range(1,7) if cmp(self.__applied_common_transform("C",vertical_transform), Generator(self.problem).generate_transforms("C", str(figure))) == 0]

              if solutions:
                return solutions[0]

            # If we have an angular common transform and are trying to apply to a circle, toss the rotation
            solutions = [str(figure) for figure in range(1,7) if cmp(self.__applied_common_transform("C",common_transform, {'circle':'angle'}), Generator(self.problem).generate_transforms("C", str(figure))) == 0]
            if solutions:
              return solutions[0]

      # Do we have an exact match?
      #print "Candidate: " + str(candidate)
      #print "Transform: " + str(Generator(self.problem).generate_transforms("C", str(1)))
      #print "Result: " + str(cmp(candidate, Generator(self.problem).generate_transforms("C", str(1))))

      solutions = [str(figure) for figure in range(1,7) if cmp(candidate, Generator(self.problem).generate_transforms("C", str(figure))) == 0]

      if solutions:
        return solutions[0]

      # Do we have a match if we fuzzy the angles?
      solutions = [str(figure) for figure in range(1,7) if cmp(candidate, Generator(self.problem).generate_transforms("C", str(figure), [], True)) == 0]

      if solutions:
        return solutions[0]

      #Given just the set of transforms, can I match each to a transform between C and an answer?

    return "7"

  # Return a set of common transforms I can apply to generate a possible solution
  def __common_transform(self, transforms):
    common_transforms = {}

    # Grab any set of transforms
    sample_transforms = transforms[0]

    # Does every object have this exact set of transforms?
    common = True
    for transform in transforms:
      if not (cmp(transform, sample_transforms) == 0):
        common = False

    if common:
      return sample_transforms

    return False

  # Does the supplied set of transforms hit every object in the supplied figure?
  def __all_objects_transformed(self, figure_name, transforms):
    figure          = self.__retrieve_figure(figure_name)
    figure_objects  = figure.getObjects()

    if len(figure_objects) != len(transforms):
      return False

    return True

  def __applied_common_transform(self, figure_name, common_transform, ignore_per_shape = {}):
    figure              = self.__retrieve_figure(figure_name)
    figure_objects      = figure.getObjects()
    new_transform       = {}
    filtered_transform  = common_transform

    for obj in figure_objects:
      # Get shape
      for attribute in obj.getAttributes():
        if attribute.getName() == 'shape':
          shape = attribute.getValue()

      if shape in ignore_per_shape.keys():
        filtered_transform = {key: value for key, value in common_transform.items() if key != ignore_per_shape[shape]}

      if filtered_transform:
        new_transform[obj.getName()] = filtered_transform

    return new_transform

  def __retrieve_figure(self, figure_name):
    figure = self.problem.getFigures().get(figure_name)
    if not figure:
      raise FigureNotFoundError("Figure not found: " + figure_name)

    return figure



class FigureNotFoundError(Exception): pass
