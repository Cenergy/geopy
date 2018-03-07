# coding = utf-8
# pylint: disable=C0103,C0301,C0303,C0410,C1801,W0640

import os, time, math
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select

class Publisher:
    """The class for auto-publish geoserver wmts service.
    """
    def __init__(self, url, user='admin', pwd='geoserver'):
        self.__ws__ = 'szhyj'
        self.__ws_uri_ = 'http://www.luojiadeyi.com/'
        self.__layer_group__ = 'beijing'
        self.__epsg__ = 'EPSG:4490'
        self.__gridset__ = '4326'
        self.__tile_size__ = '256,256'
        self.__opacity_color__ = '000000'
        self.__data_type__ = {
            '.tif' : 'GeoTIFF',
            '.img' : 'ERDASImg'
        }

        self.brower = webdriver.Chrome()
        self.brower.get(url)
        self.brower.implicitly_wait(5)
        self.__login(user, pwd)

    def __del__(self):
        self.__logout()

    @staticmethod
    def __set_e_value__(e, v, over='true'):
        if over:
            e.clear()
        e.send_keys(v)

    def set_workspace(self, ws_):
        self.__ws__ = ws_

    def set_workspace_uri(self,ws_uri_):
        self.__ws_uri_ = ws_uri_

    def set_layer_group(self,layer_group__):
        self.__layer_group__ = layer_group__

    def set_epsg(self,epsg__):
        self.__epsg__ = epsg__

    def set_gridset(self,gridset__):
        self.__gridset__ = gridset__

    def set_tile_size(self,tile_size__):
        self.__tile_size__ = tile_size__

    def set_opacity_color(self,opacity_color__):
        self.__opacity_color__ = opacity_color__

    def __login(self, user, pwd):
        """Login to geoserver administrator page.

        Arguments:
            user {string} -- user-name for geoserver administrator page
            pwd {string} -- user-password for geoserver administrator page
        """

        path = '//*[@id="header"]/div/div/span[1]/form/button'
        WebDriverWait(self.brower, 4).until(
            expected_conditions.presence_of_element_located((By.XPATH, path))
        )

        user_element = self.brower.find_element_by_id('username')
        pwd_element = self.brower.find_element_by_id('password')
        login_click = self.brower.find_element_by_xpath(path)
        if user_element and pwd_element:
            Publisher.__set_e_value__(user_element, user)
            Publisher.__set_e_value__(pwd_element, pwd)
            login_click.click()

    def __logout(self):
        """Logout to geoserver administrator page.
        """
        path = '//*[@id="header"]/div/div/span[3]/form/button'
        WebDriverWait(self.brower, 4).until(
            expected_conditions.presence_of_element_located((By.XPATH, path))
        )

        self.brower.find_element_by_xpath(path).click()

    def publish(self, dataDir):
        """publish all data in dataDir, including subdir.
        
        Arguments:
            dataDir {string} -- the data directory to publish.
        """
        # for window's path format
        dataDir = dataDir.replace('\\', '/')
        # for window's error format
        # dataDir = dataDir.replace('\', '/')

        if not self.__ensure_workspace():
            return

        layers_added = 0
        for root, dirs, files in os.walk(dataDir):
            for file in files:
                url_ = 'file:data/' + root
                name_ = self.__add_datastore(root, file)
                if name_ and self.__publish_layer(name):
                    self.__update_layer_group(name)
                    layers_added=layers_added+1

        if layers_added > 0:
            self.__seed_gwc()

    def __ensure_workspace(self):
        """ensure workspace __ws__ existed, if not, create it.
        """

        path_ = '//*[@id="navigation"]/li[2]/ul/li[2]/a/span'
        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.XPATH, path_))
        )

        self.brower.find_element_by_xpath(path_).click()

        path_ = '//*[@id="page"]/div[2]/div[1]/table/tbody'
        ws_row_ = self.__row_of_table_item(('1', self.__ws__), path_, self.__ws__)
        if ws_row_ is not None:
            print('workspace %s already existed.'%self.__ws__)
        else:
            # create new workspace.
            self.brower.find_element_by_xpath('//*[@id="page"]/div[1]/div[2]/ul/li[1]/a').click()

            WebDriverWait(self.brower, 2).until(
                expected_conditions.presence_of_element_located((By.ID, 'name'))
            )

            Publisher.__set_e_value__(self.brower.find_element_by_id('name'), self.__ws__)
            uri_ = self.__ws_uri_ + self.__ws__
            Publisher.__set_e_value__(self.brower.find_element_by_id('uri'), uri_)
            self.brower.find_element_by_id('default').click()

            self.brower.find_element_by_xpath('//*[@id="page"]/div[2]/form/ul/li[4]/a').click()

            ws_row_ = self.__row_of_table_item(('1', self.__ws__), path_, self.__ws__)
            if ws_row_ is None:
                print('workspace %s create failed, please contact administrator.'%self.__ws__)
                return False

        # edit workspace for ensure wms wfs wcs wmts service.
        ws_row_.find_element_by_xpath('.//td[1]/span/a/span').click()

        path_ = '//*[@id="tableBody"]/fieldset[2]/div/ul'
        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.XPATH, path_))
        )

        service_ = self.brower.find_element_by_xpath(path_)
        for i in range(1, 5):
            w_service = service_.find_element_by_xpath('.//li[' + str(i) + ']/input')
            if not w_service.is_selected():
                w_service.click()

        self.brower.find_element_by_xpath('//*[@id="page"]/div[2]/form/ul/li[5]/a').click()
        return True

    def __add_datastore(self, dir_, file_):
        """add a geotiff datastore with parameters.

        Arguments:
            tif {string} -- tif file
            name {string} -- datastore name
        """

        fi_names = os.path.splitext(file_)
        if not fi_names[1] in self.__data_type__:
            return

        path_ = '//*[@id="navigation"]/li[2]/ul/li[3]/a/span'
        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.XPATH, path_))
        )

        self.brower.find_element_by_xpath(path_).click()

        name_ = fi_names[0]
        full_file_ = os.path.join(dir_, file_)

        path_ = '//*[@id="page"]/div[2]/div[1]/table/tbody'
        if self.__row_of_table_item(('2', self.__ws__, '3', name_), path_, name_):
            print('datastore %s already existed.'%full_file_)
            return False

        # create new datastore.
        self.brower.find_element_by_xpath('//*[@id="page"]/div[1]/div[2]/ul/li[1]/a').click()

        type_ = self.__data_type__[fi_names[1]]
        path_ = '//*[@id="page"]/div[2]/form/ul/li[2]/div[2]/a/span'
        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.XPATH, path_))
        )

        # for GeoTIFF
        self.brower.find_element_by_xpath(path_).click()

        path_ = '//*[@id="page"]/div[2]/form/ul/li[2]/fieldset/div[1]/div/select'
        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.XPATH, path_))
        )

        fieldset_ = self.brower.find_element_by_xpath('//*[@id="page"]/div[2]/form/ul/li[2]/fieldset')
        # workspace selected
        Select(fieldset_.find_element_by_xpath('.//div[1]/div/select')).select_by_visible_text(self.__ws__)
        # set datastore name
        Publisher.__set_e_value__(fieldset_.find_element_by_xpath('.//div[2]/div/input'), name)
        # set datastore description
        Publisher.__set_e_value__(
            fieldset_.find_element_by_xpath('div[3]/div/input'), 'datastore created with %s automatically'%tif)

        # set datastore source tif file
        path_ = '//*[@id="page"]/div[2]/form/ul/li[3]/div/fieldset/div/span/div[1]/input'
        Publisher.__set_e_value__(self.brower.find_element_by_xpath(path_), 'file://' + tif)

        # 确定
        self.brower.find_element_by_xpath('//*[@id="page"]/div[2]/form/div[4]/a[1]').click()
        return True

    def __publish_layer(self, name, isnew_data):
        """public layer for new-added datastore.
        
        Arguments:
            name {string} -- the name for new layer.
            isnew_data {bool} -- is layer added for new datastore.
        """
        if not isnew_data:
            path_ = '//*[@id="navigation"]/li[2]/ul/li[4]/a/span'
            WebDriverWait(self.brower, 2).until(
                expected_conditions.presence_of_element_located((By.XPATH, path_))
            )

            self.brower.find_element_by_xpath(path_).click()

            ws_name_ = self.__ws__ + ':' + name
            path_ = '//*[@id="page"]/div[2]/div[1]/table/tbody'
            if self.__row_of_table_item(('3', ws_name_), path_, name):
                print('layer %s already existed.'%name)
                return True

            path_ = '//*[@id="page"]/div[1]/div[2]/ul/li[1]/a'
            self.brower.find_element_by_xpath(path_).click()

            path_ = '//*[@id="page"]/div[2]/form/select'
            WebDriverWait(self.brower, 2).until(
                expected_conditions.presence_of_element_located((By.XPATH, path_))
            )

            Select(self.brower.find_element_by_xpath(path_)).select_by_visible_text(ws_name_)

        path_ = '//*[@id="page"]/div[2]/div[1]/div[2]/div/table/tbody'
        publish_row_ = self.__row_of_table_item(('3', '发布'), path_, '', 1800 if isnew_data else 3)
        if publish_row_ is None:
            print('problem may have occured in server, please restart web server.')
            return False

        # click 发布 button.
        publish_row_.find_element_by_xpath('.//td[3]/span/a/span').click()

        WebDriverWait(self.brower, 5).until(
            expected_conditions.presence_of_element_located((By.ID, 'declaredSRS'))
        )

        publisher.__set_e_value__(
            self.brower.find_element_by_xpath('//*[@id="declaredSRS"]/input'), self.__epsg__)
        # override parameters
        over_field_ = self.brower.find_element_by_xpath(
            '//*[@id="page"]/div[2]/form/div[2]/div[2]/div[2]/div/ul/li/fieldset/ul/li')
        Publisher.__set_e_value__(
            over_field_.find_element_by_xpath('.//div[1]/span/span/input'), self.__opacity_color__)
        Publisher.__set_e_value__(
            over_field_.find_element_by_xpath('.//div[2]/span/div/input'), self.__tile_size__)

        path_ = '//*[@id="page"]/div[2]/form/div[2]/div[1]/ul/li[2]/a/span'
        self.brower.find_element_by_xpath(path_).click()

        WebDriverWait(self.brower, 5).until(
            expected_conditions.presence_of_element_located((By.ID, 'opaqueEnabled'))
        )

        self.brower.find_element_by_id('opaqueEnabled').click()
        self.brower.find_element_by_xpath('//*[@id="page"]/div[2]/form/div[3]/a[1]').click()
        return True

    def __update_layer_group(self, name):
        """[summary]
        
        Arguments:
            name {[type]} -- [description]
        """

        path_ = '//*[@id="navigation"]/li[2]/ul/li[5]/a/span'
        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.XPATH, path_))
        )

        self.brower.find_element_by_xpath(path_).click()

        path_ = '//*[@id="page"]/div[2]/div[1]/table/tbody'
        lg_row = self.__row_of_table_item(('1', self.__layer_group__), path_, self.__layer_group__)
        if lg_row is not None:
            # click the layer-group for update.
            lg_row.find_element_by_xpath('.//td[1]/span/a/span').click()

            WebDriverWait(self.brower, 2).until(
                expected_conditions.presence_of_element_located((By.ID, 'name'))
            )

            path_ = '//*[@id="page"]/div[2]/form/div[2]/div[2]/ul/li[10]/div/fieldset/ul/li[3]/div'
            while True:
                if self.__row_of_table_item(('3@span', self.__ws__ + ':' + name), path_ + '/table/tbody'):
                    print('layer %s already existed in group %s'%(name, self.__layer_group__))
                    return
                next_page_ = self.brower.find_element_by_xpath(path_ + '/span/span[1]/a[3]')
                if not next_page_.is_enabled():
                    break
                next_page_.click()
        else:
            # create new layer-group.
            self.brower.find_element_by_xpath('//*[@id="page"]/div[1]/div[2]/ul/li[1]/a').click()

            WebDriverWait(self.brower, 2).until(
                expected_conditions.presence_of_element_located((By.ID, 'name'))
            )

            Publisher.__set_e_value__(self.brower.find_element_by_id('name'), self.__layer_group__)
            Publisher.__set_e_value__(self.brower.find_element_by_id('title'), self.__layer_group__)
            # select workspace.
            path_ = '//*[@id="page"]/div[2]/form/div[2]/div[2]/ul/li[4]/select'
            Select(self.brower.find_element_by_xpath(path_)).select_by_visible_text(self.__ws__)

        # add new layer to layer group.
        self.brower.find_element_by_xpath(
            '//*[@id="page"]/div[2]/form/div[2]/div[2]/ul/li[10]/div/fieldset/ul/li[1]/a').click()

        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'wicket-modal'))
        )

        path_ = '//*[@class="w_content"]/div/table/tbody'
        layer_row = self.__row_of_table_item(('1', name), path_, name)
        if layer_row is None:
            print('error, the new added layer %s cannot be found.'%name)
            return

        # click layer item for adding to group
        layer_row.find_element_by_xpath('.//td[1]/span/a/span').click()

        WebDriverWait(self.brower, 2).until_not(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'wicket-modal'))
        )

        # 生成边界
        path_ = '//*[@id="page"]/div[2]/form/div[2]/div[2]/ul/li[6]/input[1]'
        self.brower.find_element_by_xpath(path_).click()
        time.sleep(0.5)

        self.brower.find_element_by_xpath('//*[@id="page"]/div[2]/form/div[3]/a[1]').click()

    def __seed_gwc(self):
        """[summary]
        """

        path_ = '//*[@id="navigation"]/li[5]/ul/li[1]/a/span'
        WebDriverWait(self.brower, 2).until(
            expected_conditions.presence_of_element_located((By.XPATH, path_))
        )

        self.brower.find_element_by_xpath(path_).click()

        ws_name = self.__ws__ + ':' + self.__layer_group__
        path_ = '//*[@id="page"]/div[2]/div[1]/table/tbody'
        tiled_layer = self.__row_of_table_item(('2', ws_name), path_, ws_name)
        if tiled_layer is None:
            print('gwc tiled layer %s not existed.'%ws_name)
            return

        # click Seed/Truncate link.
        tiled_layer.find_element_by_xpath('.//td[8]/span/div/a[1]').click()

        # switch to latest tab-page
        self.brower.switch_to.window(self.brower.window_handles[-1])
        # start seed task, thread should be 1, otherwise task will failed.
        self.brower.find_element_by_xpath('//*[@id="seed"]/table/tbody/tr[8]/td[2]/input').click()

    def __row_of_table_item(self, cmps, tbody, filter_='', wait=2):
        """find item in table satisfy cmps condition, or None.

        Arguments:
            cmps {couple} -- the compare condition.
        """

        if cmps is None or (len(cmps) == 0):
            print('judge condition is empty.')
            return

        WebDriverWait(self.brower, wait).until(
            expected_conditions.presence_of_element_located((By.XPATH, tbody))
        )

        if filter_:
            e_filter = self.brower.find_element_by_id('filter')
            Publisher.__set_e_value__(e_filter, filter_ + Keys.ENTER)

            WebDriverWait(self.brower, wait).until(
                expected_conditions.presence_of_element_located((By.XPATH, tbody))
            )

        time.sleep(0.1)
        tbody_ = self.brower.find_element_by_xpath(tbody)
        try:
            if tbody_.size['height'] == 0:
                return
            rows_ = tbody_.find_elements_by_tag_name('tr')
        except: # pylint: disable=W0702
            print('tbody element attach failed, %s'%tbody)
            return

        f_path = lambda p: './/td[' + p[0] + ']/' + (p[1] if len(p) > 1 else 'span/a/span')
        cmp_pv = [(f_path(cmps[i - 1].split('@')), cmps[i]) for i in range(1, len(cmps), 2)]

        f_cmp = lambda r, p, v: r.find_element_by_xpath(p).text == v
        f_cmp_all = lambda r: all([f_cmp(r, pv[0], pv[1]) for pv in cmp_pv])

        return next((r for r in rows_ if f_cmp_all(r)), None)


if __name__ == '__main__':
    """
        the data should be stored in a server, can't be moved after published.
        you can store data in path as you wish, and publish that path.
        or store data in data-dir of geoserver(tomcat/webapps/geoserver/data),
        which you can publish with relate path. eg. data/data/szhyj/
    """
    publisher = Publisher('http://localhost:8086/geoserver/web/')
    publisher.publish('d:/dev/map/beijing-2/')
