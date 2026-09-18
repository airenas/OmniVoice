cfg?=Makefile.options
-include $(cfg)

#####################################################################################
#### INFO
#####################################################################################
info:
	@echo "work_dir: $(work_dir)"
	@echo "corpus_dir: $(corpus_bucket)"
	@echo "config: $(config)"
	@echo "finetune_output: $(finetune_output)"
	@echo "type: $(type)"
	@echo "nvidia-smi: 		$$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv | tail -n1)"
	@echo "cuda visible dev: 	$$(echo $$CUDA_VISIBLE_DEVICES)"
	@echo "python: 			$$(python --version)"
	@echo "torch: 			$$(python -c 'import torch; print(torch.__version__)')"
	@echo "torchaudio: 		$$(python -c 'import torchaudio; print(torchaudio.__version__)')"
	@echo "cuda in python: 	$$(python -c 'import torch; print(torch.version.cuda) if torch.cuda.is_available() else "N/A"')"
.PHONY: info	
#####################################################################################
log?=INFO
python_cmd=PYTHONPATH=./ LOGLEVEL=$(log) python3
python_omni_cmd=PYTHONPATH=./../../ LOGLEVEL=$(log) python3
#####################################################################################
#####################################################################################
#### PREPARE CORPUS
#####################################################################################
#####################################################################################
$(work_dir) $(work_dir)/corpus/extracted $(work_dir)/corpus/lab $(work_dir)/corpus/range \
	$(work_dir)/corpus/final $(work_dir)/corpus/final/wavs $(work_dir)/corpus/wav \
	$(work_dir)/finetune/data $(work_dir)/finetune/exp/omnivoice_finetune:
	mkdir -p $@
#####################################################################################
speaker?=NER
lab_prefix?=NER
freq?=24000

$(work_dir)/corpus/.dwn.done: | $(work_dir)
	mcli cp $(corpus_bucket) $(work_dir)/corpus/dwn/ -r
	touch $@
############################################
$(work_dir)/corpus/extracted/utf8.mlf: $(work_dir)/corpus/.dwn.done | $(work_dir)/corpus/extracted
	iconv -f ISO-8859-13 -t UTF-8 $(work_dir)/corpus/dwn/metadata.mlf > $@
############################################
$(work_dir)/corpus/extracted/fixed.mlf: $(work_dir)/corpus/extracted/utf8.mlf | $(work_dir)/corpus/lab
	pv $^ | $(python_cmd) ./local/exclude_files.py --exclude "$(exclude_files)" \
		| $(python_cmd) ./local/fix_mlf.py \
		| $(python_cmd) ./local/change_name.py --prefix '$(speaker)_' --strip-prefix '$(lab_prefix)' > $@
############################################
$(work_dir)/corpus/extracted/fixed.split.mlf: $(work_dir)/corpus/extracted/fixed.mlf $(work_dir)/corpus/range/.done
	pv $(work_dir)/corpus/extracted/fixed.mlf | $(python_cmd) ./local/mlf_by_range.py --rangeDir $(work_dir)/corpus/range > $@_
	mv $@_ $@
############################################
$(work_dir)/corpus/lab/.done: $(work_dir)/corpus/extracted/fixed.mlf | $(work_dir)/corpus/lab
	pv $^ | $(python_cmd) ./local/split_mlf.py --outDir `dirname $@`
	touch $@
############################################
$(work_dir)/corpus/range/.done: $(work_dir)/corpus/lab/.done | $(work_dir)/corpus/range
	ls -1 $(work_dir)/corpus/lab/*.lab | xargs -n1 -I {} -P 4 sh -c \
		'base=`basename {} .lab`; \
		cat {} | $(python_cmd) ./local/mlf_to_range.py --max-sil 400 --max-duration 20000 > $(work_dir)/corpus/range/$${base}.split.range'
	touch $@
############################################
$(work_dir)/corpus/wav/split.sh: $(work_dir)/corpus/range/.done | $(work_dir)/corpus/wav
	rm -f $@_
	ls -1 $(work_dir)/corpus/range/*.range | xargs -n1 -I {} sh -c \
		'base=`basename {} .split.range`; \
		cat {} | $(python_cmd) ./local/range_to_split_sh.py --name $${base} --in-dir $(corpus_wav_dir) --out-dir $(work_dir)/corpus/wav \
			--strip-prefix '$(speaker)_' >> $@_'
	mv $@_ $@	
	chmod +x $@
############################################
$(work_dir)/corpus/wav/.done: $(work_dir)/corpus/wav/split.sh
	$(work_dir)/corpus/wav/split.sh
	touch $(work_dir)/corpus/wav/.done
############################################
$(work_dir)/corpus/extracted/metadata.csv: $(work_dir)/corpus/extracted/fixed.split.mlf
	pv $< | $(python_cmd) ./local/mlf_to_csv.py --outputPhones --skipSP > $@_
	mv $@_ $@
$(work_dir)/corpus/final/metadata.csv: $(work_dir)/corpus/extracted/metadata.csv | $(work_dir)/corpus/final
	pv $< | sed '/noise/d' | sort > $@_
	mv $@_ $@

############################################
$(work_dir)/corpus/extracted/audio.samples: $(work_dir)/corpus/final/wavs/.done
	ls -1 $(work_dir)/corpus/final/wavs/*.wav | sort | pv | $(python_cmd) ./local/audio_to_samples.py > $@_
	mv $@_ $@
############################################
$(work_dir)/corpus/extracted/exclude.files: $(work_dir)/corpus/extracted/metadata.csv
	cat $< | grep 'noise' | awk -F'|' '{print $$1}' > $@_
	mv $@_ $@
############################################
$(work_dir)/corpus/final/wavs/.done: $(work_dir)/corpus/wav/.done $(work_dir)/corpus/extracted/exclude.files | $(work_dir)/corpus/final/wavs
	for wav in $(work_dir)/corpus/wav/*.wav; do \
		base=`basename $${wav} .wav`; \
		base=$$(echo $${base} | sed s/lab_//g); \
# 		echo "Copy wav $${base}"; \
# 		cp $${wav} $(work_dir)/corpus/final/wavs/$${base}.wav; \
		echo "Converting WAV to $(freq) Hz 16 bit for $${base}"; \
		sox $${wav} -r $(freq) -b 16 $(work_dir)/corpus/final/wavs/$${base}.wav; \
	done
	echo "Drop exluded files"
	cat $(work_dir)/corpus/extracted/exclude.files | xargs -n 1 -I {} sh -c 'rm $(work_dir)/corpus/final/wavs/{}.wav'
	touch $(work_dir)/corpus/final/wavs/.done
############################################
test/corpus/len: $(work_dir)/corpus/final/wavs/.done
	ls -1 $(work_dir)/corpus/final/wavs/*.wav | xargs -n1 soxi -D | $(python_local_cmd) -c "import sys; print(f'{sum(float(x) for x in sys.stdin)/3600:.3f}h')"
############################################
type ?= gr
$(work_dir)/.corpus.prepare.done: $(work_dir)/corpus/final/metadata.csv $(work_dir)/corpus/final/wavs/.done
	touch $@
$(work_dir)/corpus/final/all.jsonl: $(work_dir)/.corpus.prepare.done
	$(python_cmd) ./local/csv_to_jsonl.py --input $(work_dir)/corpus/final/metadata.csv --output $(work_dir)/corpus/final/all.jsonl_ \
		--audio-dir $(work_dir)/corpus/final/wavs --type=$(type)
	mv $(work_dir)/corpus/final/all.jsonl_ $(work_dir)/corpus/final/all.jsonl

prepare/corpus: $(work_dir)/.corpus.prepare.done
.PHONY: prepare/corpus

$(work_dir)/corpus/final/dev.jsonl $(work_dir)/corpus/final/train.jsonl: $(work_dir)/corpus/final/all.jsonl
	$(python_cmd) ./local/split_jsonl.py --input $(work_dir)/corpus/final/all.jsonl --dev-output $(work_dir)/corpus/final/dev.jsonl_ \
		--train-output $(work_dir)/corpus/final/train.jsonl_
	mv $(work_dir)/corpus/final/dev.jsonl_ $(work_dir)/corpus/final/dev.jsonl
	mv $(work_dir)/corpus/final/train.jsonl_ $(work_dir)/corpus/final/train.jsonl

prepare/json: $(work_dir)/corpus/final/dev.jsonl $(work_dir)/corpus/final/train.jsonl
.PHONY: prepare/json

#####################################################################################
#### PREPARE FOR FINETUNE
#####################################################################################
$(work_dir)/finetune/data/.%.prepare.done: $(work_dir)/corpus/final/%.jsonl $(work_dir)/.corpus.prepare.done | $(work_dir)/finetune/data
	$(python_omni_cmd) -m omnivoice.scripts.extract_audio_tokens \
            --input_jsonl "$(work_dir)/corpus/final/$*.jsonl" \
			--tar_output_pattern "$(work_dir)/finetune/data/$*/audios/shard-%06d.tar" \
			--jsonl_output_pattern "$(work_dir)/finetune/data/$*/txts/shard-%06d.jsonl" \
            --tokenizer_path eustlb/higgs-audio-v2-tokenizer \
            --nj_per_gpu 3 --shuffle True
	touch $@
prepare/finetune: $(work_dir)/finetune/data/.dev.prepare.done $(work_dir)/finetune/data/.train.prepare.done
.PHONY: prepare/finetune
#####################################################################################
#####################################################################################
config?=./config/train.config.json
finetune_output?=$(work_dir)/finetune/exp/omnivoice_finetune

$(work_dir)/finetune/data.json: $(work_dir)/finetune/data/.dev.prepare.done $(work_dir)/finetune/data/.train.prepare.done | $(work_dir)/finetune
	printf '%s\n' '{"train": [{"manifest_path": ["$(work_dir)/finetune/data/train/data.lst"]}],' \
	'  "dev": [{"manifest_path": ["$(work_dir)/finetune/data/dev/data.lst"]}]}' > $@

finetune: $(work_dir)/finetune/.done
GPU_IDS?=0,1,2
NUM_GPUS?=3
$(work_dir)/finetune/.done: $(work_dir)/finetune/data/.train.prepare.done $(work_dir)/finetune/data.json | $(work_dir)/finetune/exp/omnivoice_finetune
	accelerate launch --gpu_ids "${GPU_IDS}" --num_processes ${NUM_GPUS} -m omnivoice.cli.train \
		--train_config $(config) \
        --data_config $(work_dir)/finetune/data.json \
        --output_dir $(finetune_output)
#####################################################################################
jupyter: 
	jupyter lab ./ --ip=0.0.0.0 --port=8888 --no-browser		
#####################################################################################
clean:
	@echo -n "Are you sure to delete $(work_dir)? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(work_dir)
.PHONY: clean
#####################################################################################
.EXPORT_ALL_VARIBLES:	
