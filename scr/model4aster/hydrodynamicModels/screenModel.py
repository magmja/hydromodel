"""
-------------------------------------------\n
-         University of Stavanger          \n
-         Hui Cheng (PhD student)          \n
-          Lin Li (Medveileder)            \n
-      Prof. Muk Chen Ong (Supervisor)     \n
-------------------------------------------\n
Any questions about this code,
please email: hui.cheng@uis.no \n
Modules can be used to calculate the hydrodynamic forces on nets.
In order to use this module, we recommend ``import screenModel as sm`` in the beginning of your code.
Please refer to Cheng et al. (2020) [https://doi.org/10.1016/j.aquaeng.2020.102070] for details.
"""
import numpy as np

row = 1025  # [kg/m3]   sea water density
kinematic_viscosity = 1.004e-6  # when the water temperature is 20 degree.
dynamic_viscosity = 1.002e-3  # when the water temperature is 20 degree.
CD_udv = 0
CL_udv = 0


class forceModel:
    """
    For Morison hydrodynamic models, the forces on netting are calculated based on individual a panel section of netting.
    The twines and knots in the net panel are considered as an integrated structure. In this module, the net panel is defined by
    three nodes because three (non-colinear) points can determine a unique plane in Euclidean geometry.
    In practice, the force is usually decomposed into two componnets: drag force F_D and lift force F_L (Cheng et al., 2020).
    """

    def __init__(self, model_index, hydro_element, solidity, dwh=0.0, dw0=0.0):
        """
        :param model_index: [string] Unit: [-]. To indicate the model function, e.g.: 'S1', 'S2', 'S3'.
        :param hydro_element: [[list]] Unit: [-]. A python list to indicate how the net panel are connected. e.g.:[[p1,p2,p3][p2,p3,p4,p5]...]. If the input net panel contains 4 nodes, it will automaticly decomposed to 3 node net panel.
        :param solidity: [float] Unit: [-]. The solidity of netting.
        :param dwh: [float] Unit: [m]. The hydrodynamic diameter of the numerical net twines. It is used for the force calculation (reference area)
        :param dw0: [float] Unit: [m]. The diameter of the physical net twines. It is used for the hydrodynamic coefficients.
        """
        self.modelIndex = str(model_index)
        self.hydro_element = convert_hydro_element(hydro_element)
        self.dwh = dwh
        self.dw0 = dw0
        self.Sn = solidity
        self.force_on_elements = np.zeros((len(self.hydro_element), 3))

    def output_hydro_element(self):
        """
        :return: [[list]] of the indexes of points in elements. e.g.:[[1,2,3],[2,3,4]...]
        """
        return self.hydro_element

    def hydro_coefficients(self, inflow_angle, current_velocity, knot=False):
        """
        :return:
        :param inflow_angle: [float] Unit [rad]. Definition: the angle between normal vector of a net panel and the flow direction
        :param current_velocity: [np.array].shape=(1,3) Unit: [m/s]. The current velocity [ux,uy,uz] in cartesian coordinate system.
        :param knot: [boolean] knot option. *Default=False*
        :return: drag and lift force coefficients. [float] Unit: [-].
        """
        drag_coefficient, lift_coefficient = 0, 0
        if self.modelIndex not in 'S1,S2,S3,S4,S5,S6,UDV,bi2014':
            print("The selected hydrodynamic model is not included in the present program")
            exit()
        elif self.modelIndex == 'S1':  # aarsnes 1990
            drag_coefficient = 0.04 + (-0.04 + self.Sn - 1.24 * pow(self.Sn, 2) + 13.7 * pow(self.Sn, 3)) * np.cos(
                inflow_angle)
            lift_coefficient = (0.57 * self.Sn - 3.54 * pow(self.Sn, 2) + 10.1 * pow(self.Sn, 3)) * np.sin(
                2 * inflow_angle)

        elif self.modelIndex == 'S2':  # Loland 1991
            drag_coefficient = 0.04 + (
                    -0.04 + 0.33 * self.Sn + 6.54 * pow(self.Sn, 2) - 4.88 * pow(self.Sn, 3)) * np.cos(
                inflow_angle)
            lift_coefficient = (-0.05 * self.Sn + 2.3 * pow(self.Sn, 2) - 1.76 * pow(self.Sn, 3)) * np.sin(
                2 * inflow_angle)

        elif self.modelIndex == 'S3':  # Kristiansen 2012
            a1 = 0.9
            a3 = 0.1
            b2 = 1.0
            b4 = 0.1
            reynolds_number = row * self.dw0 * np.linalg.norm(current_velocity) / dynamic_viscosity / (
                    1 - self.Sn)  # Re
            cd_cylinder = -78.46675 + 254.73873 * np.log10(reynolds_number) - 327.8864 * pow(np.log10(reynolds_number),
                                                                                             2) + 223.64577 * pow(
                np.log10(reynolds_number), 3) - 87.92234 * pow(
                np.log10(reynolds_number), 4) + 20.00769 * pow(np.log10(reynolds_number), 5) - 2.44894 * pow(
                np.log10(reynolds_number), 6) + 0.12479 * pow(np.log10(reynolds_number), 7)
            cd_zero = cd_cylinder * (self.Sn * (2 - self.Sn)) / (2.0 * pow((1 - self.Sn), 2))
            cn_pi_4 = 0.5 * cd_cylinder * self.Sn / pow(1 - self.Sn, 2)
            cl_pi_4 = (0.5 * cd_zero - np.pi * cn_pi_4 / (8 + cn_pi_4)) / np.sqrt(2)
            drag_coefficient = cd_zero * (a1 * np.cos(inflow_angle) + a3 * np.cos(3 * inflow_angle))
            lift_coefficient = cl_pi_4 * (b2 * np.sin(2 * inflow_angle) + b4 * np.sin(4 * inflow_angle))

        elif self.modelIndex == 'S4':  # Fridman 1973
            reynolds_number = np.linalg.norm(current_velocity) * self.dw0 * row / dynamic_viscosity
            reynolds_star = reynolds_number / (2 * self.Sn)
            coe_tangent = 0.1 * pow(reynolds_number, 0.14) * self.Sn
            coe_normal = 3 * pow(reynolds_star, -0.07) * self.Sn
            drag_coefficient = coe_normal * np.cos(inflow_angle) * pow(np.cos(inflow_angle), 2) + coe_tangent * np.sin(
                inflow_angle) * pow(
                np.sin(inflow_angle), 2)
            lift_coefficient = coe_normal * np.sin(inflow_angle) * pow(np.cos(inflow_angle), 2) + coe_tangent * np.cos(
                inflow_angle) * pow(
                np.sin(inflow_angle), 2)
        elif self.modelIndex == 'S5':  # Lee 2005 # polynomial fitting
            drag_coefficient = 0.556 * pow(inflow_angle, 7) - 1.435 * pow(inflow_angle, 6) - 2.403 * pow(
                inflow_angle, 5) + 11.75 * pow(inflow_angle, 4) - 13.48 * pow(inflow_angle, 3) + 5.079 * pow(
                inflow_angle, 2) - 0.9431 * pow(inflow_angle, 1) + 1.155
            lift_coefficient = -10.22 * pow(inflow_angle, 9) + 69.22 * pow(inflow_angle, 8) - 187.9 * pow(
                inflow_angle, 7) + 257.3 * pow(inflow_angle, 6) - 181.6 * pow(inflow_angle, 5) + 59.14 * pow(
                inflow_angle, 4) - 7.97 * pow(inflow_angle, 3) + 2.103 * pow(
                inflow_angle, 2) + 0.2325 * pow(inflow_angle, 1) + 0.01294

        elif self.modelIndex == 'S6':  # Balash 2009
            reynolds_cylinder = row * self.dw0 * np.linalg.norm(current_velocity) / dynamic_viscosity / (
                    1 - self.Sn) + 0.000001
            cd_cylinder = 1 + 10.0 / (pow(reynolds_cylinder, 2.0 / 3.0))
            drag_coefficient = cd_cylinder * (0.12 - 0.74 * self.Sn + 8.03 * pow(self.Sn, 2)) * pow(inflow_angle, 3)
            if knot:
                mesh_size = 10 * self.dw0  # assume Sn=0.2
                diameter_knot = 2 * self.dw0  # assume the knot is twice of the diameter of the twine
                reynolds_sphere = row * diameter_knot * np.linalg.norm(current_velocity) / dynamic_viscosity / (
                        1 - self.Sn) + 0.000001
                coe_sphere = 24.0 / reynolds_sphere + 6.0 / (1 + np.sqrt(reynolds_sphere)) + 0.4
                drag_coefficient = (cd_cylinder * 8 * pow(diameter_knot,
                                                          2) + coe_sphere * np.pi * mesh_size * self.dw0) / np.pi * mesh_size * self.dw0 * (
                                           0.12 - 0.74 * self.Sn + 8.03 * pow(self.Sn, 2)) * pow(inflow_angle, 3)
            else:
                pass
        elif self.modelIndex == 'UDV':  # Lee 2005 # polynomial fitting
            drag_coefficient = CD_udv
            lift_coefficient = CL_udv

        elif self.modelIndex == 'bi2014':  # from Table 1 in Bi et al., 2014, JFS
            p1 = 0.1873
            p2 = 0.4921
            p3 = 0.04
            drag_coefficient = p3 + p2 * np.cos(inflow_angle) + p1 * pow(np.cos(inflow_angle), 2)
            p1 = -0.169
            p2 = 0.4159
            p3 = 0
            lift_coefficient = p3 + p2 * np.sin(2 * inflow_angle) + p1 * pow(np.sin(2 * inflow_angle), 2)

        return drag_coefficient, lift_coefficient

    def force_on_element(self, net_wake, realtime_node_position, current_velocity, velocity_nodes=np.zeros((99999, 3)),
                         wave=False, fe_time=0):
        """
        :param velocity_nodes: [np.array].shape=(1,3) Unit [m/s]. The structural velocity of nodes [ux,uy,uz] in cartesian coordinate system.
        :param net_wake: A object wake model, net2net wake model. Must create first.
        :param realtime_node_position: [np.array].shape=(N,3) Unit: [m]. The coordinates of N nodes in cartesian coordinate system.
        :param current_velocity: [np.array].shape=(1,3) Unit [m/s]. The current velocity [ux,uy,uz] in cartesian coordinate system.
        :param wave:  A wake model object. *Default value=False* Must create first.
        :param fe_time: [float] Unit [s]. The time in Code_Aster. *Default value=0* Must give if wave is added.
        :param current_velocity: numpy array ([ux,uy,uz]), Unit [m/s]
        :return: [np.array].shape=(M,3) Unit [N]. The hydrodynamic forces on all M elements. Meanwhile, update the self.hydroForces_Element
        """
        wave_velocity = np.zeros((len(self.hydro_element), 3))
        if wave:
            for index, panel in enumerate(self.hydro_element):
                element_center = (realtime_node_position[int(panel[0])] + realtime_node_position[int(panel[1])] +
                                  realtime_node_position[int(panel[2])]) / 3
                wave_velocity[index] = wave.get_velocity(element_center, fe_time)
        hydro_force_on_element = []  # force on net panel, initial as zeros
        for index, panel in enumerate(self.hydro_element):  # loop based on the hydrodynamic elements
            p1 = realtime_node_position[panel[0]]
            p2 = realtime_node_position[panel[1]]
            p3 = realtime_node_position[panel[2]]
            velocity_structure = (velocity_nodes[panel[0]] + velocity_nodes[panel[1]] + velocity_nodes[panel[2]]) / (
                len(panel))
            alpha, lift_direction, net_area = calculation_on_element(p1, p2, p3, np.array(current_velocity))
            # calculate the inflow angel, normal vector, lift force factor, area of the hydrodynamic element
            velocity = np.array(current_velocity) * net_wake.reduction_factor(index, alpha) + wave_velocity[index]
            # if not in the wake region, the effective velocity is the undisturbed velocity
            while np.linalg.norm(velocity_structure) > np.linalg.norm(velocity):
                velocity_structure *= 0.1
            if np.dot(velocity_structure, velocity) > 0:
                velocity_relative = velocity - velocity_structure
            else:
                velocity_relative = velocity - velocity_structure * 0
            drag_coefficient, lift_coefficient = self.hydro_coefficients(alpha, velocity_relative, knot=False)
            fd = 0.5 * row * net_area * drag_coefficient * np.linalg.norm(velocity_relative) * velocity_relative
            fl = 0.5 * row * net_area * lift_coefficient * pow(np.linalg.norm(velocity_relative), 2) * lift_direction
            hydro_force_on_element.append((fd + fl) / 2.0)
        if np.size(np.array(hydro_force_on_element)) == np.size(self.hydro_element):
            self.force_on_elements = np.array(hydro_force_on_element)
            return np.array(hydro_force_on_element)
        else:
            print("\nError! the size of hydrodynamic force on element is not equal to the number of element."
                  "\nPlease cheack you code.")
            print("\nThe size of element is " + str(len(self.hydro_element)))
            print("\nThe size of hydrodynamic force is " + str(len(np.array(hydro_force_on_element))))
            exit()

    def screen_fsi(self, realtime_node_position, velocity_on_element, velocity_of_nodes=np.zeros((9999, 3))):
        """
        :param realtime_node_position: [np.array].shape=(N,3) Unit: [m]. The coordinates of N nodes in cartesian coordinate system.
        :param velocity_on_element: [np.array].shape=(M,3) Unit [m/s]. The current velocity [ux,uy,uz] on all net panels in cartesian coordinate system.
        :param velocity_of_nodes: [np.array].shape=(N,3) Unit: [m/s]. The velocities of N nodes in cartesian coordinate system.
        :return: update the self.hydroForces_Element and output the forces on all the net panels.
        """
        # print("The length of U vector is " + str(len(velocity_on_element)))
        hydro_force_on_element = []  # force on net panel, initial as zeros
        # print("velocity elementy is 1" + str(velocity_on_element))
        # print("velocity_of_nodes is " + str(velocity_of_nodes))
        # print("realtime_node_position is " + str(realtime_node_position))
        if len(velocity_on_element) < len(self.hydro_element):
            print("position is " + str(realtime_node_position))
            print("Velocity is " + str(velocity_of_nodes))
            print("velocity elements is " + str(velocity_on_element))
            exit()
        for index, panel in enumerate(self.hydro_element):  # loop based on the hydrodynamic elements
            p1 = realtime_node_position[panel[0]]
            p2 = realtime_node_position[panel[1]]
            p3 = realtime_node_position[panel[2]]
            alpha, lift_direction, surface_area = calculation_on_element(p1, p2, p3, velocity_on_element[index])
            drag_coefficient, lift_coefficient = self.hydro_coefficients(alpha, velocity_on_element[index], knot=False)

            velocity_fluid = velocity_on_element[index] * np.sqrt(2.0 / (2.0 - drag_coefficient - lift_coefficient))
            velocity_structure = (velocity_of_nodes[panel[0]] + velocity_of_nodes[panel[1]] + velocity_of_nodes[
                panel[2]]) / (len(panel))
            while np.linalg.norm(velocity_structure) > np.linalg.norm(velocity_fluid):
                velocity_structure *= 0.1
            if np.dot(velocity_structure, velocity_fluid) > 0:
                velocity_relative = velocity_fluid - velocity_structure
            else:
                velocity_relative = velocity_fluid - velocity_structure * 0

            fd = 0.5 * row * surface_area * drag_coefficient * np.linalg.norm(np.array(velocity_relative)) * np.array(
                velocity_relative)
            fl = 0.5 * row * surface_area * lift_coefficient * pow(np.linalg.norm(velocity_relative),
                                                                   2) * lift_direction
            hydro_force_on_element.append((fd + fl) / 2.0)
        if np.size(np.array(hydro_force_on_element)) == np.size(self.hydro_element):
            self.force_on_elements = np.array(hydro_force_on_element)
            return np.array(hydro_force_on_element)
        else:
            print("Error!, the size of hydrodynamic force on element is not equal to the number of element."
                  "Please cheack you code.")
            exit()

    # def distribute_velocity(self, current_velocity, wave_velocity=0):
    #     """
    #     :param current_velocity:
    #     :param wave_velocity:
    #     :return:
    #     """
    #     velocity_on_element = []  # velocity on net panel, initial as zeros
    #     if len(current_velocity) < 4:
    #         velocity_on_element = np.ones((len(self.hydro_element), 3)) * current_velocity
    #     elif len(current_velocity) == len(self.hydro_element):
    #         velocity_on_element = np.array(current_velocity)
    #
    #     if not wave_velocity == 0:
    #         for panel in self.hydro_element:  # loop based on the hydrodynamic elements
    #             velocity_on_element[self.hydro_element.index(panel)] = +wave_velocity[self.hydro_element.index(panel)]
    #     if len(velocity_on_element) == len(self.hydro_element):
    #         return velocity_on_element
    #     else:
    #         print("\nError! the size of velocity on element is not equal to the number of element."
    #               "\nPlease cheack you code.")
    #         print("\nThe size of element is " + str(len(self.hydro_element)))
    #         print("\nThe size of hydrodynamic force is " + str(len(velocity_on_element)))
    #         exit()

    def distribute_force(self, number_of_node, force_increasing_factor=1):
        """
        Transfer the forces on line element to their corresponding nodes.\n
        :return: [np.array].shape=(N,3) Unit [N]. The hydrodynamic forces on all N nodes.
        """
        forces_on_nodes = np.zeros((number_of_node, 3))  # force on nodes, initial as zeros
        for index, panel in enumerate(self.hydro_element):
            forces_on_nodes[panel[0]] += force_increasing_factor * (self.force_on_elements[index]) / 3
            forces_on_nodes[panel[1]] += force_increasing_factor * (self.force_on_elements[index]) / 3
            forces_on_nodes[panel[2]] += force_increasing_factor * (self.force_on_elements[index]) / 3
        return forces_on_nodes


# - five functions used in the current file
def get_distance(p1, p2):
    """
    Module private function.\n
    :param p1: point1 [np.array].shape=(1,3) or a [list] of coordinates Unit: [m].
    :param p2: point2 [np.array].shape=(1,3) or a [list] of coordinates Unit: [m].
    :return: The distance between two points.  [float] Unit [m].
    """

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    return np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)


def get_orientation(p1, p2):
    """
    Module private function.\n
    :param p1: point1 [np.array].shape=(1,3) or a [list] of coordinates Unit: [m].
    :param p2: point2 [np.array].shape=(1,3) or a [list] of coordinates Unit: [m].
    :return: The unit vector from p1 to p2.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    p = np.array([dx, dy, dz])
    return p / np.linalg.norm(p)


def calculation_on_element(point1, point2, point3, velocity):
    """
    Moudule private function.\n
    :param point1: point1 [np.array].shape=(1,3) or a [list] of coordinates Unit: [m].
    :param point2: point2 [np.array].shape=(1,3) or a [list] of coordinates Unit: [m].
    :param point3: point3 [np.array].shape=(1,3) or a [list] of coordinates Unit: [m].
    :param velocity: [np.array].shape=(1,3) Unit: [m/s]. Flow velocity
    :return: inflow angle [float][rad], lift vector[np.array].shape=(1,3) [-], area of net panel [float][m^2]
    """
    # because the mesh construction, the first two node cannot have same index
    a1 = get_orientation(point1, point2)
    a2 = get_orientation(point1, point3)
    ba1 = get_distance(point1, point2)
    ba2 = get_distance(point1, point3)
    normal_vector = np.cross(a1, a2) / np.linalg.norm(np.cross(a1, a2))
    if np.dot(normal_vector, velocity) < 0:
        normal_vector = -normal_vector
    surface_area = 0.5 * np.linalg.norm(np.cross(a1 * ba1, a2 * ba2))
    lift_vector = np.cross(np.cross(velocity, normal_vector), velocity) / \
                  np.linalg.norm(np.cross(np.cross(velocity, normal_vector), velocity) + 0.000000001)

    coin_alpha = abs(np.dot(normal_vector, velocity) / np.linalg.norm(velocity))
    alpha = np.arccos(coin_alpha)
    return alpha, lift_vector, surface_area


def convert_hydro_element(elements):
    """
    :param elements: [[list]] Unit: [-]. A list of indexes of elements which can contain 4 or 3 nodes.
    :return: [[list]] Unit: [-]. A list of indexes of elements only contain 3 nodes.
    """
    hydro_elements = []
    for panel in elements:  # loop based on the hydrodynamic elements
        if len([int(k) for k in set(panel)]) <= 3:  # the hydrodynamic element is a triangle
            hydro_elements.append([k for k in set([int(k) for k in set(panel)])])  # a list of the node sequence
        else:
            for i in range(len(panel)):
                nodes = [int(k) for k in panel]  # get the list of nodes [p1,p2,p3,p4]
                nodes.pop(i)  # delete the i node to make the square to a triangle
                hydro_elements.append(nodes)  # delete the i node to make the square to a triangle
    return hydro_elements
