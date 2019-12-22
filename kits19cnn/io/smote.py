import numpy as np
from collections import defaultdict

class SliceIDSampler(object):
    def __init__(self, pos_per_slice_dict, classes_ratio=[0.33, 0.33, 0.34],
                 shuffle=True, random_state=42):
        """
        Attributes:
            pos_per_slice_dict (dict): generated by io.Preprocessor.save_dir_as_2d()
                - classes_per_slice.json
                    the keys are not cases, but the actual filenames that are
                    being read.
                        {
                            case_slice_idx_str: [classes_in_slice],
                            case_slice_idx_str2: [classes_in_slice],
                        }
            classes_ratio (list): probability distribution of how often each
                class should occur
            shuffle (bool): whether or not to shuffle the sampled case slice
                list
            random_state (int): Seed for random sampling.
        """
        self.pos_per_slice_dict = pos_per_slice_dict
        self.cases_slice_list = list(pos_per_slice_dict.keys())
        self.classes_ratio = classes_ratio
        self.num_classes = len(classes_ratio)
        self.shuffle = shuffle
        self.random_state = random_state

        self.total_num_slices = len(self.cases_slice_list)
        self.classes = list(range(self.num_classes))

        assert np.sum(classes_ratio) == 1, \
            "classes_ratio must add up to 1."
        print(f"Randomly sampling {self.total_num_slices} slices to match the",
              f"distribution, {self.classes_ratio}, with",
              f"classes, {self.classes}, and seed, {self.random_state}.")

    def sample_slices_names(self):
        """
        Use the case_slice_idx_str directly. However, it is randomly sampled from
        a dictionary of each class with the slice indices (pos_slice_dict).
        Returns:
            list of randomly sampled (case, slice_idx) tuples that matches the
            desired class_ratio
        """
        np.random.seed(self.random_state)

        final_cases_slice_list = []
        freq_distr = self.find_new_slice_freq_distribution()
        # sampling the actual case_slice names based on the sampled frequency distribution
        for class_label, freq in enumerate(freq_distr):
            for i in range(freq):
                sampled_name = np.random.choice(self.classes_dict[label_idx])
                final_cases_slice_list.append(sampled_name)

        assert len(final_cases_slice_list) == self.total_num_slices, \
            f"The final cases list must be of length, {self.total_num_slices}"
        if self.shuffle:
            np.random.shuffle(final_cases_slice_list)
        return final_cases_slice_list

    def find_new_slice_freq_distribution(self):
        """
        Determines the number of slices per class using the class ratio
        and the total number of slices.
        """
        np.random.seed(self.random_state)

        slices_per_class_raw = np.array(self.classes_ratio)*self.total_num_slices
        slices_per_class = slices_per_class_raw.astype(np.int32)

        if np.sum(slices_per_class) == self.total_num_slices:
            print(f"Using {slices_per_class} slices per class.")
        elif np.sum(slices_per_class) < self.total_num_slices:
            # NOTE: ^ Here, there may be non-exact numbers of slices because
            # of rounding. However, we'll deal with this by sampling from the
            # undersampled classes wrt the classes_ratio:
            undersampled_bool = slices_per_class < slices_per_class_raw
            undersampled_classes = self.classes[undersampled_bool]
            num_left = self.total_num_slices - np.sum(slices_per_class)
            for i in range(num_left):
                sampled_class = np.random.choice(undersampled_classes)
                slices_per_class[sampled_class] += 1
            print(f"Oversampled undersampled classes to {slices_per_class}")
        elif np.sum(slices_per_class) > self.total_num_slices:
            # Undersampling oversampled classes
            # This probably won't happen because .astype(np.int32) rounds down
            oversampled_bool = slices_per_class > slices_per_class_raw
            oversampled_classes = self.classes[oversampled_bool]
            num_left = np.sum(slices_per_class) - self.total_num_slices
            for i in range(num_left):
                sampled_class = np.random.choice(oversampled_classes)
                slices_per_class[sampled_class] -= 1
            print(f"Undersampled oversampled classes to {slices_per_class}")

        assert np.sum(slices_per_class) == self.total_num_slices, \
            "The frequency distribution of the sampled slices must match " + \
            "the total number of slices."
        return slices_per_class

    def parse_dict(self):
        """
        Creates a dictionary:
        {
            class_label1: [case_slice_str1, case_slice_str2,...],
            class_label2: [case_slice_str3, case_slice_str4,...],
            class_label3: [case_slice_str5, case_slice_str6,...],
            ...
        }
        from self.pos_per_slice_dict

        Done for cleaner class sampling.
        """
        self.classes_dict = defaultdict(list)
        for case_slice in self.cases_slice_list:
            for label_idx in self.pos_per_slice_dict[case_slice]:
                self.classes_dict[label_idx].append(case_slice)
